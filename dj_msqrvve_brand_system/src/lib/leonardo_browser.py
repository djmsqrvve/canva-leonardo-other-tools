"""Leonardo.ai browser automation — generation via headless Firefox."""
from __future__ import annotations

import time

from lib.browser.driver import BrowserBase
from lib.errors import BrowserPreflightError

try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
except ModuleNotFoundError:
    By = None  # type: ignore[assignment,misc]
    EC = None  # type: ignore[assignment,misc]
    WebDriverWait = None  # type: ignore[assignment,misc]

GENERATE_BUTTON_XPATH = "//button[contains(., 'Generate')]"
PROMPT_TEXTAREA_SELECTOR = "textarea[placeholder*='Type a prompt']"
GALLERY_IMAGE_SELECTOR = "img[src*='cdn.leonardo.ai']"
DIALOG_OVERLAY_SELECTOR = "[data-slot='dialog-overlay']"
LEONARDO_LOGIN_URL = "https://app.leonardo.ai/auth/login"
LEONARDO_IMAGE_GENERATION_URL = "https://app.leonardo.ai/image-generation"
AUTH_PAGE_MARKERS = ("continue with google", "sign in", "log in", "login")
GENERATION_TIMEOUT_SECONDS = 180
GENERATION_POLL_INTERVAL_SECONDS = 2.0

# Re-export for backward compat with tests that import these
from lib.browser.profile import (  # noqa: E402
    SESSION_FILES,
    find_default_source_profile as _find_default_source_profile,
)


class LeonardoBrowser(BrowserBase):
    """Automated browser flow for Leonardo image generation."""

    SITE_NAME = "Leonardo"

    def _is_auth_page(self) -> bool:
        return self.is_auth_page(markers=AUTH_PAGE_MARKERS)

    def _wait_for_dashboard_ready(self, timeout_seconds: int = 30) -> None:
        WebDriverWait(self.driver, timeout_seconds).until(
            EC.presence_of_element_located((By.XPATH, GENERATE_BUTTON_XPATH))
        )

    def _collect_generation_image_urls(self, limit: int = 8) -> list[str]:
        urls: list[str] = []
        seen: set[str] = set()
        for image in self.driver.find_elements(By.CSS_SELECTOR, GALLERY_IMAGE_SELECTOR):
            src = (image.get_attribute("src") or "").strip()
            if not src or src.startswith("data:") or src in seen:
                continue
            if "/generations/" not in src:
                continue
            seen.add(src)
            urls.append(src)
            if len(urls) >= limit:
                break
        return urls

    def _wait_for_generation_results(
        self,
        existing_urls: set[str],
        *,
        timeout_seconds: int = GENERATION_TIMEOUT_SECONDS,
        poll_interval_seconds: float = GENERATION_POLL_INTERVAL_SECONDS,
    ) -> list[str]:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self._is_auth_page():
                self.raise_session_expired(
                    "generation-session-expired",
                    "Leonardo redirected to auth while waiting for generation results.",
                )
            current_urls = self._collect_generation_image_urls()
            new_urls = [url for url in current_urls if url not in existing_urls]
            if new_urls:
                return new_urls[:4]
            time.sleep(poll_interval_seconds)

        artifacts = self.capture_failure(
            "generation-timeout",
            f"No new images within {timeout_seconds}s.",
        )
        from lib.browser.artifacts import format_artifact_hint

        raise RuntimeError(
            f"Leonardo generation timed out after {timeout_seconds}s. "
            f"{format_artifact_hint(artifacts)}"
        )

    def login(self) -> None:
        print("Navigating to Leonardo login...")
        self.driver.get(LEONARDO_LOGIN_URL)

        try:
            self._wait_for_dashboard_ready()
            print("Successfully logged in (detected dashboard).")
            return
        except Exception as exc:  # noqa: BLE001
            if self.headless:
                try:
                    self.raise_session_expired(
                        "login-headless-session",
                        "Headless login check could not detect a valid Leonardo session.",
                    )
                except BrowserPreflightError as refresh_error:
                    raise refresh_error from exc

        print("Interactive login required. Complete sign-in in the browser window.")
        deadline = time.time() + self.login_timeout_seconds
        while time.time() < deadline:
            try:
                self._wait_for_dashboard_ready(timeout_seconds=5)
                print("Login detected! Proceeding...")
                return
            except Exception:  # noqa: BLE001
                time.sleep(2)

        artifacts = self.capture_failure(
            "login-timeout",
            f"Login not completed within {self.login_timeout_seconds}s.",
        )
        from lib.browser.artifacts import format_artifact_hint

        raise BrowserPreflightError(
            f"Login not completed within {self.login_timeout_seconds}s. "
            f"{format_artifact_hint(artifacts)}"
        )

    def generate(self, prompt: str) -> list[str]:
        print(f"Triggering generation for prompt: '{prompt[:50]}...'")
        self.driver.get(LEONARDO_IMAGE_GENERATION_URL)

        if self._is_auth_page():
            self.raise_session_expired(
                "generation-auth-required",
                "Leonardo redirected to login before generation page loaded.",
            )

        self.dismiss_modals(
            labels=["let's go", "let's go!", "got it", "ok", "okay",
                    "close", "dismiss", "continue", "skip", "start creating"]
        )
        time.sleep(1.0)
        self.dismiss_modals()

        try:
            existing_urls = set(self._collect_generation_image_urls())
            prompt_input = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, PROMPT_TEXTAREA_SELECTOR))
            )
            prompt_input.clear()
            prompt_input.send_keys(prompt)

            generate_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, GENERATE_BUTTON_XPATH))
            )
            generate_btn.click()

            print("Generate button clicked! Waiting for results...")
            return self._wait_for_generation_results(existing_urls)
        except BrowserPreflightError:
            raise
        except Exception as exc:  # noqa: BLE001
            artifacts = self.capture_failure(
                "generation-selector-failure",
                f"{type(exc).__name__}: {exc}",
            )
            from lib.browser.artifacts import format_artifact_hint

            raise RuntimeError(
                f"Leonardo generation failed. {format_artifact_hint(artifacts)}"
            ) from exc
