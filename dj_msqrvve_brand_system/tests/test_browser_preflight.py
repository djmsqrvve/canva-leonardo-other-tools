import json
from pathlib import Path

import pytest

from lib.errors import BrowserPreflightError
from lib.leonardo_browser import LeonardoBrowser


class DummyDriver:
    def __init__(self):
        self.visited_urls = []
        self.current_url = "https://app.leonardo.ai/image-generation"
        self.page_source = "<html><body>dashboard</body></html>"

    def get(self, url):
        self.visited_urls.append(url)

    def save_screenshot(self, path):
        Path(path).write_bytes(b"fake-png")
        return True


def test_headless_mode_requires_existing_profile(tmp_path):
    browser = LeonardoBrowser.__new__(LeonardoBrowser)
    browser.headless = True
    browser.profile_path = tmp_path

    with pytest.raises(BrowserPreflightError, match="existing browser profile"):
        browser._ensure_profile_supports_mode()


def test_login_fails_fast_in_headless_mode_without_saved_session():
    browser = LeonardoBrowser.__new__(LeonardoBrowser)
    browser.headless = True
    browser.driver = DummyDriver()
    browser.artifact_root = Path("/tmp/test-artifacts")
    browser._wait_for_dashboard_ready = lambda timeout_seconds=30: (_ for _ in ()).throw(RuntimeError("no session"))

    with pytest.raises(BrowserPreflightError, match="without --headless"):
        browser.login()


def test_capture_failure_artifacts_writes_page_and_metadata(tmp_path):
    browser = LeonardoBrowser.__new__(LeonardoBrowser)
    browser.headless = True
    browser.artifact_root = tmp_path
    browser.driver = DummyDriver()

    artifacts = browser.capture_failure("selector-failure", "generate button missing")

    screenshot_path = Path(artifacts["screenshot"])
    page_source_path = Path(artifacts["page_source"])
    metadata_path = Path(artifacts["metadata"])

    assert screenshot_path.exists()
    assert page_source_path.read_text(encoding="utf-8") == "<html><body>dashboard</body></html>"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["phase"] == "selector-failure"
    assert metadata["reason"] == "generate button missing"
    assert metadata["headless"] is True
    assert metadata["current_url"] == "https://app.leonardo.ai/image-generation"


def test_wait_for_generation_results_returns_new_urls():
    browser = LeonardoBrowser.__new__(LeonardoBrowser)
    browser.headless = True

    observed_urls = iter(
        [
            ["https://example.com/existing.png"],
            [
                "https://example.com/existing.png",
                "https://example.com/new-1.png",
                "https://example.com/new-2.png",
            ],
        ]
    )

    browser._is_auth_page = lambda: False
    browser._collect_generation_image_urls = lambda: next(observed_urls)

    result = browser._wait_for_generation_results(
        {"https://example.com/existing.png"},
        timeout_seconds=1,
        poll_interval_seconds=0,
    )

    assert result == [
        "https://example.com/new-1.png",
        "https://example.com/new-2.png",
    ]


def test_generate_requires_session_refresh_when_login_redirect_detected():
    browser = LeonardoBrowser.__new__(LeonardoBrowser)
    browser.headless = True
    browser.driver = DummyDriver()
    browser.wait = None

    calls = []

    browser._is_auth_page = lambda: True

    def raise_session_expired(phase, reason):
        calls.append((phase, reason))
        raise BrowserPreflightError("refresh required")

    browser.raise_session_expired = raise_session_expired

    with pytest.raises(BrowserPreflightError, match="refresh required"):
        browser.generate("shadowpunk skyline")

    assert calls == [
        (
            "generation-auth-required",
            "Leonardo redirected to login before generation page loaded.",
        )
    ]
