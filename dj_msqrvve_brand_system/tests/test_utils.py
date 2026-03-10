import pytest
from unittest.mock import patch, MagicMock

from lib.errors import ApiResponseError, TimeoutError
from lib.utils import compute_backoff_schedule, download_to_file, poll_job


def test_compute_backoff_schedule():
    delays = compute_backoff_schedule(
        attempts=4,
        initial_delay_seconds=1.0,
        backoff_factor=2.0,
        max_delay_seconds=3.0,
    )
    assert delays == [1.0, 2.0, 3.0, 3.0]


def test_poll_job_success():
    calls = {"count": 0}

    def fetcher(_job_id):
        calls["count"] += 1
        if calls["count"] == 1:
            return {"job": {"status": "PENDING"}}
        return {"job": {"status": "SUCCESS", "result": {"value": 1}}}

    payload = poll_job(
        "job_1",
        "example",
        fetcher,
        status_extractor=lambda body: body["job"]["status"],
        success_statuses=("success",),
        failure_statuses=("failed",),
        max_attempts=3,
        initial_delay_seconds=0,
        sleep_fn=lambda _seconds: None,
    )
    assert payload["job"]["result"]["value"] == 1
    assert calls["count"] == 2


def test_poll_job_failure():
    def fetcher(_job_id):
        return {"status": "FAILED"}

    with pytest.raises(ApiResponseError):
        poll_job(
            "job_2",
            "example",
            fetcher,
            status_extractor=lambda body: body["status"],
            success_statuses=("success",),
            failure_statuses=("failed",),
            max_attempts=2,
            initial_delay_seconds=0,
            sleep_fn=lambda _seconds: None,
        )


def test_download_to_file_empty_response(tmp_path):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.content = b""

    with patch("lib.utils.requests.get", return_value=mock_response):
        with pytest.raises(ApiResponseError, match="empty response"):
            download_to_file("https://example.com/img.png", str(tmp_path / "out.png"))


def test_download_to_file_html_content_type(tmp_path):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.content = b"<html>error</html>"
    mock_response.headers = {"content-type": "text/html; charset=utf-8"}

    with patch("lib.utils.requests.get", return_value=mock_response):
        with pytest.raises(ApiResponseError, match="text/html"):
            download_to_file("https://example.com/img.png", str(tmp_path / "out.png"))


def test_poll_job_timeout():
    def fetcher(_job_id):
        return {"status": "PENDING"}

    with pytest.raises(TimeoutError):
        poll_job(
            "job_3",
            "example",
            fetcher,
            status_extractor=lambda body: body["status"],
            success_statuses=("success",),
            failure_statuses=("failed",),
            max_attempts=2,
            initial_delay_seconds=0,
            sleep_fn=lambda _seconds: None,
        )
