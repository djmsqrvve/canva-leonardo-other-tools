"""Shared exception types for API and pipeline flows."""

from __future__ import annotations

from typing import Optional

import requests


class ApiResponseError(RuntimeError):
    """Raised for non-success API responses or request failures."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


class AuthError(ApiResponseError):
    """Raised when authentication/authorization fails."""


class RateLimitError(ApiResponseError):
    """Raised when APIs reject calls due to rate limiting."""


class TimeoutError(ApiResponseError):
    """Raised when requests or asynchronous jobs time out."""


def raise_for_http_error(response: requests.Response) -> None:
    """Map HTTP status failures into typed exceptions."""
    status_code = response.status_code
    body = response.text
    message = f"API request failed ({status_code}) for {response.request.method} {response.url}"

    if status_code in (401, 403):
        raise AuthError(message, status_code=status_code, response_body=body)
    if status_code == 429:
        raise RateLimitError(message, status_code=status_code, response_body=body)
    raise ApiResponseError(message, status_code=status_code, response_body=body)


def handle_request_exception(exc: Exception, context: str) -> None:
    """Convert requests exceptions into typed project exceptions."""
    if isinstance(exc, requests.Timeout):
        raise TimeoutError(f"Request timed out during {context}") from exc
    if isinstance(exc, requests.RequestException):
        raise ApiResponseError(f"Request failed during {context}: {exc}") from exc
    raise
