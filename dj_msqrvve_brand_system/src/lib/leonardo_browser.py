from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

from lib.errors import BrowserPreflightError, OptionalDependencyError

SELENIUM_IMPORT_ERROR = None

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager
except ModuleNotFoundError as exc:  # pragma: no cover - exercised via preflight tests
    SELENIUM_IMPORT_ERROR = exc
    webdriver = None
    Options = None
    Service = None
    By = None
    EC = None
    WebDriverWait = None
    ChromeDriverManager = None


LOGIN_BUTTON_XPATH = "//button[contains(., 'Generate')]"
PROMPT_TEXTAREA_SELECTOR = "textarea[placeholder*='Type a prompt']"
GALLERY_IMAGE_SELECTOR = "img.generation-image"
CHROME_CANDIDATES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium-browser",
    "chromium",
    "chrome",
)


def _bootstrap_command() -> str:
    return 'python src/main.py generate-browser "your prompt"'


class LeonardoBrowser:
    """Automated browser flow for local Leonardo generation."""

    def __init__(self, headless: bool = False, login_timeout_seconds: int = 300):
        self.headless = headless
        self.login_timeout_seconds = login_timeout_seconds
        self.profile_path = Path(__file__).resolve().parent.parent.parent / "user_profile"

        self._ensure_optional_dependencies()
        self.chrome_binary = self._resolve_chrome_binary()
        self._ensure_profile_supports_mode()
        self.profile_path.mkdir(parents=True, exist_ok=True)

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")

        chrome_options.add_argument(f"user-data-dir={self.profile_path}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        if self.chrome_binary:
            chrome_options.binary_location = self.chrome_binary

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options,
        )
        self.wait = WebDriverWait(self.driver, 30)

    def _ensure_optional_dependencies(self) -> None:
        if SELENIUM_IMPORT_ERROR is None:
            return
        raise OptionalDependencyError(
            "Browser generation requires optional dependencies. "
            "Install dj_msqrvve_brand_system/requirements-browser.txt to enable it."
        ) from SELENIUM_IMPORT_ERROR

    def _resolve_chrome_binary(self) -> str | None:
        explicit_binary = os.environ.get("CHROME_BINARY", "").strip()
        if explicit_binary:
            if Path(explicit_binary).exists():
                return explicit_binary
            raise BrowserPreflightError(
                f"CHROME_BINARY points to '{explicit_binary}', but that path does not exist."
            )

        for candidate in CHROME_CANDIDATES:
            resolved = shutil.which(candidate)
            if resolved:
                return resolved

        raise BrowserPreflightError(
            "Chrome/Chromium was not found on PATH. Install Chrome locally or set CHROME_BINARY."
        )

    def _profile_has_session_data(self) -> bool:
        if not self.profile_path.exists():
            return False
        return any(self.profile_path.iterdir())

    def _ensure_profile_supports_mode(self) -> None:
        # Headless mode is only safe once the interactive login has already populated the profile.
        if self.headless and not self._profile_has_session_data():
            raise BrowserPreflightError(
                "Headless browser generation requires an existing logged-in Chrome profile. "
                f"Run {_bootstrap_command()} without --headless once to bootstrap the session."
            )

    def _wait_for_dashboard_ready(self, timeout_seconds: int = 30) -> None:
        local_wait = WebDriverWait(self.driver, timeout_seconds)
        local_wait.until(
            EC.presence_of_element_located((By.XPATH, LOGIN_BUTTON_XPATH))
        )

    def login(self):
        """Open Leonardo and ensure the current profile is authenticated."""
        print("Navigating to Leonardo login...")
        self.driver.get("https://app.leonardo.ai/auth/login")

        try:
            self._wait_for_dashboard_ready()
            print("Successfully logged in (detected dashboard).")
            return
        except Exception as exc:  # noqa: BLE001
            if self.headless:
                raise BrowserPreflightError(
                    "Headless browser generation requires a valid saved Leonardo session. "
                    f"Re-run {_bootstrap_command()} without --headless to log in interactively."
                ) from exc

        print("Interactive login required. Complete the sign-in flow in the browser window.")
        deadline = time.time() + self.login_timeout_seconds
        while time.time() < deadline:
            try:
                self._wait_for_dashboard_ready(timeout_seconds=5)
                print("Login detected! Proceeding...")
                return
            except Exception:  # noqa: BLE001
                time.sleep(2)

        raise BrowserPreflightError(
            f"Interactive login was not completed within {self.login_timeout_seconds} seconds."
        )

    def generate(self, prompt: str, model_id=None):
        """
        Automate prompt entry and trigger generation in the Leonardo web UI.

        The selector set is intentionally centralized because Leonardo updates can break it.
        """
        del model_id  # Browser mode currently drives the default web UI only.
        print(f"Triggering generation for prompt: '{prompt[:50]}...'")
        self.driver.get("https://app.leonardo.ai/image-generation")

        try:
            prompt_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, PROMPT_TEXTAREA_SELECTOR))
            )
            prompt_input.clear()
            prompt_input.send_keys(prompt)

            generate_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, LOGIN_BUTTON_XPATH))
            )
            generate_btn.click()

            print("Generate button clicked! Waiting for results...")
            time.sleep(30)

            images = self.driver.find_elements(By.CSS_SELECTOR, GALLERY_IMAGE_SELECTOR)
            return [img.get_attribute("src") for img in images[:4] if img.get_attribute("src")]
        except Exception as exc:  # noqa: BLE001
            print(f"Error during generation: {exc}")
            return []

    def close(self):
        self.driver.quit()
