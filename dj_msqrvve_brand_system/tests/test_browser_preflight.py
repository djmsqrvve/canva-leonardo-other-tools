import pytest

from lib.errors import BrowserPreflightError
from lib.leonardo_browser import LeonardoBrowser


def test_headless_mode_requires_existing_profile(tmp_path):
    browser = LeonardoBrowser.__new__(LeonardoBrowser)
    browser.headless = True
    browser.profile_path = tmp_path

    with pytest.raises(BrowserPreflightError, match="logged-in Chrome profile"):
        browser._ensure_profile_supports_mode()


def test_login_fails_fast_in_headless_mode_without_saved_session():
    browser = LeonardoBrowser.__new__(LeonardoBrowser)
    browser.headless = True
    browser.driver = type("Driver", (), {"get": lambda self, _url: None})()
    browser._wait_for_dashboard_ready = lambda timeout_seconds=30: (_ for _ in ()).throw(RuntimeError("no session"))

    with pytest.raises(BrowserPreflightError, match="without --headless"):
        browser.login()
