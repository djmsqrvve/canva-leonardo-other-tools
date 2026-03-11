"""Shared Firefox browser base for all site-specific automation."""
from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

from lib.errors import BrowserPreflightError, OptionalDependencyError
from lib.browser.profile import (
    find_default_source_profile,
    sync_session,
    remove_lock_files,
)
from lib.browser.artifacts import capture_failure_artifacts, format_artifact_hint

SELENIUM_IMPORT_ERROR = None
try:
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from webdriver_manager.firefox import GeckoDriverManager
except ModuleNotFoundError as exc:
    SELENIUM_IMPORT_ERROR = exc
    webdriver = None  # type: ignore[assignment]
    Options = None  # type: ignore[assignment,misc]
    Service = None  # type: ignore[assignment,misc]
    By = None  # type: ignore[assignment,misc]
    EC = None  # type: ignore[assignment,misc]
    WebDriverWait = None  # type: ignore[assignment,misc]
    GeckoDriverManager = None  # type: ignore[assignment,misc]

FIREFOX_CANDIDATES = ("firefox", "firefox-esr")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class BrowserBase:
    """Shared Firefox lifecycle: profile sync, driver init, artifacts, modals."""

    SITE_NAME: str = "unknown"

    def __init__(
        self,
        headless: bool = False,
        login_timeout_seconds: int = 300,
        profile_path: Path | str | None = None,
    ):
        self.headless = headless
        self.login_timeout_seconds = login_timeout_seconds
        self.profile_path = Path(
            profile_path
            or os.environ.get("FIREFOX_PROFILE", str(PROJECT_ROOT / "user_profile"))
        )
        self.artifact_root = PROJECT_ROOT / "outputs" / "browser-artifacts"
        self.source_profile_path = self._resolve_source_profile()

        self._ensure_deps()
        self.browser_binary = self._resolve_browser_binary()
        self._sync_profile()
        self._ensure_profile_supports_mode()

        self.driver = self._create_driver()
        self.wait = WebDriverWait(self.driver, 30)

    # -- profile & driver setup --

    def _resolve_source_profile(self) -> Path | None:
        explicit = os.environ.get("FIREFOX_SOURCE_PROFILE", "").strip()
        if explicit:
            p = Path(explicit)
            return p if p.is_dir() else None
        return find_default_source_profile()

    def _sync_profile(self) -> None:
        if self.source_profile_path is None:
            return
        copied = sync_session(self.source_profile_path, self.profile_path)
        remove_lock_files(self.profile_path)
        if copied:
            print(f"Synced {copied} session files from {self.source_profile_path}")

    def _ensure_profile_supports_mode(self) -> None:
        if self.headless and not self._profile_has_session_data():
            raise BrowserPreflightError(
                f"Headless mode requires an existing browser profile with session data. "
                f"Run once without --headless to bootstrap."
            )

    def _profile_has_session_data(self) -> bool:
        if not self.profile_path.exists():
            return False
        return any(self.profile_path.iterdir())

    def _create_driver(self):
        opts = Options()
        if self.headless:
            opts.add_argument("-headless")
        opts.add_argument("-profile")
        opts.add_argument(str(self.profile_path))
        if self.browser_binary:
            opts.binary_location = self.browser_binary
        return webdriver.Firefox(
            service=Service(GeckoDriverManager().install()),
            options=opts,
        )

    # -- dependency checks --

    def _ensure_deps(self) -> None:
        if SELENIUM_IMPORT_ERROR is None:
            return
        raise OptionalDependencyError(
            "Browser automation requires selenium + webdriver-manager. "
            "Install requirements-browser.txt."
        ) from SELENIUM_IMPORT_ERROR

    def _resolve_browser_binary(self) -> str | None:
        explicit = os.environ.get("FIREFOX_BINARY", "").strip()
        if explicit:
            if Path(explicit).exists():
                return explicit
            raise BrowserPreflightError(f"FIREFOX_BINARY path '{explicit}' does not exist.")
        for candidate in FIREFOX_CANDIDATES:
            resolved = shutil.which(candidate)
            if resolved:
                return resolved
        raise BrowserPreflightError("Firefox not found on PATH. Install Firefox or set FIREFOX_BINARY.")

    # -- shared helpers --

    def screenshot(self, name: str = "screenshot") -> str:
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        path = self.artifact_root / f"{name}.png"
        self.driver.save_screenshot(str(path))
        return str(path)

    def capture_failure(self, phase: str, reason: str) -> dict[str, str]:
        return capture_failure_artifacts(
            self.driver, self.artifact_root, phase, reason, headless=self.headless
        )

    def raise_session_expired(self, phase: str, reason: str) -> None:
        artifacts = self.capture_failure(phase, reason)
        hint = format_artifact_hint(artifacts)
        raise BrowserPreflightError(
            f"{self.SITE_NAME} session expired or login required. "
            f"Re-run without --headless to refresh. {hint}"
        )

    def dismiss_modals(self, labels: list[str] | None = None) -> bool:
        """Click a dismiss button matching any label, or force-remove overlays."""
        if labels is None:
            labels = ["let's go", "got it", "ok", "okay", "close", "dismiss", "continue", "skip"]
        dismissed = self.driver.execute_script("""
            const labels = arguments[0];
            const buttons = Array.from(document.querySelectorAll('button'));
            for (const btn of buttons) {
                if (labels.includes((btn.innerText || '').trim().toLowerCase())) {
                    btn.click();
                    return true;
                }
            }
            return false;
        """, labels)
        if dismissed:
            time.sleep(0.8)
            return True
        # Force-remove common overlay patterns
        self.driver.execute_script("""
            document.querySelectorAll("[data-slot='dialog-overlay']").forEach(el => el.remove());
            document.querySelectorAll("[data-slot='dialog-content']").forEach(el => el.remove());
            document.querySelectorAll("[role='dialog']").forEach(el => el.remove());
        """)
        time.sleep(0.5)
        return False

    def is_auth_page(self, markers: tuple[str, ...] = ()) -> bool:
        url = (getattr(self.driver, "current_url", "") or "").lower()
        if "/auth/" in url or "/login" in url:
            return True
        if markers:
            source = (getattr(self.driver, "page_source", "") or "").lower()
            return any(m in source for m in markers)
        return False

    def close(self) -> None:
        self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
