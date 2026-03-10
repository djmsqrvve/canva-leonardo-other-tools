from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

from lib.errors import BrowserPreflightError, OptionalDependencyError

SELENIUM_IMPORT_ERROR = None

try:
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from webdriver_manager.firefox import GeckoDriverManager
except ModuleNotFoundError as exc:  # pragma: no cover - exercised via preflight tests
    SELENIUM_IMPORT_ERROR = exc
    webdriver = None
    Options = None
    Service = None
    By = None
    EC = None
    WebDriverWait = None
    GeckoDriverManager = None


GENERATE_BUTTON_XPATH = "//button[contains(., 'Generate')]"
PROMPT_TEXTAREA_SELECTOR = "textarea[placeholder*='Type a prompt']"
GALLERY_IMAGE_SELECTOR = "img[src*='cdn.leonardo.ai']"
DIALOG_OVERLAY_SELECTOR = "[data-slot='dialog-overlay']"
LEONARDO_LOGIN_URL = "https://app.leonardo.ai/auth/login"
LEONARDO_IMAGE_GENERATION_URL = "https://app.leonardo.ai/image-generation"
AUTH_PAGE_MARKERS = ("continue with google", "sign in", "log in", "login")
GENERATION_TIMEOUT_SECONDS = 180
GENERATION_POLL_INTERVAL_SECONDS = 2.0
FIREFOX_CANDIDATES = (
    "firefox",
    "firefox-esr",
)


def _bootstrap_command() -> str:
    return 'python src/main.py generate-browser "your prompt"'


class LeonardoBrowser:
    """Automated browser flow for local Leonardo generation."""

    def __init__(self, headless: bool = False, login_timeout_seconds: int = 300):
        self.headless = headless
        self.login_timeout_seconds = login_timeout_seconds
        project_root = Path(__file__).resolve().parent.parent.parent
        self.profile_path = Path(
            os.environ.get("FIREFOX_PROFILE", str(project_root / "user_profile"))
        )
        self.artifact_root = project_root / "outputs" / "browser-artifacts"

        self._ensure_optional_dependencies()
        self.browser_binary = self._resolve_browser_binary()
        self._ensure_profile_supports_mode()
        self.profile_path.mkdir(parents=True, exist_ok=True)

        firefox_options = Options()
        if headless:
            firefox_options.add_argument("-headless")

        firefox_options.add_argument("-profile")
        firefox_options.add_argument(str(self.profile_path))
        if self.browser_binary:
            firefox_options.binary_location = self.browser_binary

        self.driver = webdriver.Firefox(
            service=Service(GeckoDriverManager().install()),
            options=firefox_options,
        )
        self.wait = WebDriverWait(self.driver, 30)

    def _ensure_optional_dependencies(self) -> None:
        if SELENIUM_IMPORT_ERROR is None:
            return
        raise OptionalDependencyError(
            "Browser generation requires optional dependencies. "
            "Install dj_msqrvve_brand_system/requirements-browser.txt to enable it."
        ) from SELENIUM_IMPORT_ERROR

    def _resolve_browser_binary(self) -> str | None:
        explicit_binary = os.environ.get("FIREFOX_BINARY", "").strip()
        if explicit_binary:
            if Path(explicit_binary).exists():
                return explicit_binary
            raise BrowserPreflightError(
                f"Browser binary path '{explicit_binary}' does not exist."
            )

        for candidate in FIREFOX_CANDIDATES:
            resolved = shutil.which(candidate)
            if resolved:
                return resolved

        raise BrowserPreflightError(
            "Firefox was not found on PATH. Install Firefox locally or set FIREFOX_BINARY."
        )

    def _profile_has_session_data(self) -> bool:
        if not self.profile_path.exists():
            return False
        return any(self.profile_path.iterdir())

    def _ensure_profile_supports_mode(self) -> None:
        # Headless mode is only safe once the interactive login has already populated the profile.
        if self.headless and not self._profile_has_session_data():
            raise BrowserPreflightError(
                "Headless browser generation requires an existing logged-in browser profile. "
                f"Run {_bootstrap_command()} without --headless once to bootstrap the session."
            )

    def _wait_for_dashboard_ready(self, timeout_seconds: int = 30) -> None:
        local_wait = WebDriverWait(self.driver, timeout_seconds)
        local_wait.until(
            EC.presence_of_element_located((By.XPATH, GENERATE_BUTTON_XPATH))
        )

    def _is_auth_page(self) -> bool:
        current_url = (getattr(self.driver, "current_url", "") or "").lower()
        if "/auth/" in current_url:
            return True

        page_source = (getattr(self.driver, "page_source", "") or "").lower()
        return any(marker in page_source for marker in AUTH_PAGE_MARKERS)

    def _capture_failure_artifacts(self, phase: str, reason: str) -> dict[str, str]:
        artifact_dir = self.artifact_root / f"{int(time.time() * 1000)}-{phase}"
        artifact_dir.mkdir(parents=True, exist_ok=True)

        artifacts: dict[str, str] = {}
        screenshot_path = artifact_dir / "screenshot.png"
        try:
            if self.driver.save_screenshot(str(screenshot_path)):
                artifacts["screenshot"] = str(screenshot_path)
        except Exception:  # noqa: BLE001
            pass

        page_source = getattr(self.driver, "page_source", None)
        if isinstance(page_source, str):
            page_source_path = artifact_dir / "page.html"
            page_source_path.write_text(page_source, encoding="utf-8")
            artifacts["page_source"] = str(page_source_path)

        metadata = {
            "phase": phase,
            "reason": reason,
            "headless": self.headless,
            "current_url": getattr(self.driver, "current_url", ""),
        }
        metadata_path = artifact_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        artifacts["metadata"] = str(metadata_path)
        return artifacts

    def _format_artifact_hint(self, artifacts: dict[str, str]) -> str:
        if not artifacts:
            return ""
        parts = [f"{key}={value}" for key, value in sorted(artifacts.items())]
        return f"Artifacts: {', '.join(parts)}."

    def _raise_session_refresh_required(self, phase: str, reason: str) -> None:
        artifacts = self._capture_failure_artifacts(phase, reason)
        artifact_hint = self._format_artifact_hint(artifacts)
        raise BrowserPreflightError(
            "Saved Leonardo session appears to be expired or login is required. "
            f"Re-run {_bootstrap_command()} without --headless to refresh the profile. "
            f"{artifact_hint}"
        )

    def _dismiss_modal_if_present(self) -> None:
        """Dismiss any open dialog overlay (e.g. What's New announcements).

        Uses JS to click a dismiss button by text content first, then falls back
        to forcefully removing both the overlay and dialog content from the DOM.
        """
        overlays = self.driver.find_elements(By.CSS_SELECTOR, DIALOG_OVERLAY_SELECTOR)
        if not overlays:
            return

        # Use JS to find and click a dismiss button by visible text — bypasses interactability checks
        dismissed = self.driver.execute_script("""
            const labels = ["let's go", "let's go!", "got it", "ok", "okay", "close", "dismiss", "continue", "skip", "start creating"];
            const buttons = Array.from(document.querySelectorAll('button'));
            for (const btn of buttons) {
                if (labels.includes((btn.innerText || '').trim().toLowerCase())) {
                    btn.click();
                    return true;
                }
            }
            return false;
        """)
        if dismissed:
            time.sleep(0.8)
            return

        # Force-remove the overlay and any open dialog content from the DOM
        self.driver.execute_script("""
            document.querySelectorAll("[data-slot='dialog-overlay']").forEach(el => el.remove());
            document.querySelectorAll("[data-slot='dialog-content']").forEach(el => el.remove());
            document.querySelectorAll("[role='dialog']").forEach(el => el.remove());
        """)
        time.sleep(0.5)

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
                self._raise_session_refresh_required(
                    "generation-session-expired",
                    "Leonardo redirected back to authentication while waiting for generation results.",
                )

            current_urls = self._collect_generation_image_urls()
            new_urls = [url for url in current_urls if url not in existing_urls]
            if new_urls:
                return new_urls[:4]

            time.sleep(poll_interval_seconds)

        artifacts = self._capture_failure_artifacts(
            "generation-timeout",
            f"No new Leonardo images were detected within {timeout_seconds} seconds.",
        )
        artifact_hint = self._format_artifact_hint(artifacts)
        raise RuntimeError(
            f"Leonardo browser generation did not produce new images within {timeout_seconds} seconds. "
            f"{artifact_hint}"
        )

    def login(self):
        """Open Leonardo and ensure the current profile is authenticated."""
        print("Navigating to Leonardo login...")
        self.driver.get(LEONARDO_LOGIN_URL)

        try:
            self._wait_for_dashboard_ready()
            print("Successfully logged in (detected dashboard).")
            return
        except Exception as exc:  # noqa: BLE001
            if self.headless:
                try:
                    self._raise_session_refresh_required(
                        "login-headless-session",
                        "Headless login check could not detect a valid saved Leonardo session.",
                    )
                except BrowserPreflightError as refresh_error:
                    raise refresh_error from exc

        print("Interactive login required. Complete the sign-in flow in the browser window.")
        deadline = time.time() + self.login_timeout_seconds
        while time.time() < deadline:
            try:
                self._wait_for_dashboard_ready(timeout_seconds=5)
                print("Login detected! Proceeding...")
                return
            except Exception:  # noqa: BLE001
                time.sleep(2)

        artifacts = self._capture_failure_artifacts(
            "login-timeout",
            f"Interactive login was not completed within {self.login_timeout_seconds} seconds.",
        )
        artifact_hint = self._format_artifact_hint(artifacts)
        raise BrowserPreflightError(
            f"Interactive login was not completed within {self.login_timeout_seconds} seconds. "
            f"{artifact_hint}"
        )

    def generate(self, prompt: str):
        """
        Automate prompt entry and trigger generation in the Leonardo web UI.

        The selector set is intentionally centralized because Leonardo updates can break it.
        """
        print(f"Triggering generation for prompt: '{prompt[:50]}...'")
        self.driver.get(LEONARDO_IMAGE_GENERATION_URL)

        if self._is_auth_page():
            self._raise_session_refresh_required(
                "generation-auth-required",
                "Leonardo redirected to login before the generation page loaded.",
            )

        self._dismiss_modal_if_present()
        # Also check and dismiss after a short wait in case a second modal appears
        time.sleep(1.0)
        self._dismiss_modal_if_present()

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
            artifacts = self._capture_failure_artifacts(
                "generation-selector-failure",
                f"{type(exc).__name__}: {exc}",
            )
            artifact_hint = self._format_artifact_hint(artifacts)
            raise RuntimeError(
                "Leonardo browser generation failed before results were detected. "
                f"{artifact_hint}"
            ) from exc

    def close(self):
        self.driver.quit()
