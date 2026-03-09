from types import SimpleNamespace

import pytest
import requests

from lib.errors import (
    ApiResponseError,
    AuthError,
    RateLimitError,
    TimeoutError,
    handle_request_exception,
    raise_for_http_error,
)


class DummyResponse:
    def __init__(self, status_code: int, body: str = "body"):
        self.status_code = status_code
        self.text = body
        self.url = "https://api.example.test/v1/items"
        self.request = SimpleNamespace(method="GET")


@pytest.mark.parametrize("status_code", [401, 403])
def test_raise_for_http_error_maps_auth_errors(status_code):
    with pytest.raises(AuthError) as exc:
        raise_for_http_error(DummyResponse(status_code))
    assert exc.value.status_code == status_code
    assert exc.value.response_body == "body"


def test_raise_for_http_error_maps_rate_limit():
    with pytest.raises(RateLimitError) as exc:
        raise_for_http_error(DummyResponse(429))
    assert exc.value.status_code == 429
    assert exc.value.response_body == "body"


def test_raise_for_http_error_maps_other_status_codes():
    with pytest.raises(ApiResponseError) as exc:
        raise_for_http_error(DummyResponse(500, body="internal"))
    assert exc.value.status_code == 500
    assert exc.value.response_body == "internal"


def test_handle_request_exception_maps_timeout():
    with pytest.raises(TimeoutError, match="Request timed out"):
        handle_request_exception(requests.Timeout("slow"), "GET /slow")


def test_handle_request_exception_maps_requests_error():
    with pytest.raises(ApiResponseError, match="Request failed"):
        handle_request_exception(requests.RequestException("boom"), "POST /items")


def test_handle_request_exception_reraises_non_requests_errors():
    with pytest.raises(RuntimeError, match="plain"):
        handle_request_exception(RuntimeError("plain"), "context")
