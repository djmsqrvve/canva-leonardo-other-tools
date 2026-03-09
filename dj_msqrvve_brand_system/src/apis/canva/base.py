from typing import Any, Optional

import requests

from lib.errors import handle_request_exception, raise_for_http_error
from .auth import CanvaTokenManager


class CanvaBaseClient:
    """Base class for all Canva Connect API modules."""

    BASE_URL = "https://api.canva.com/rest/v1"

    def __init__(
        self,
        access_token=None,
        *,
        token_manager: CanvaTokenManager | None = None,
        refresh_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        env_file_path: str | None = None,
        timeout_seconds: int = 30,
    ):
        self.token_manager = token_manager or CanvaTokenManager(
            access_token=access_token,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            env_file_path=env_file_path,
            timeout_seconds=timeout_seconds,
        )
        if not self.token_manager.access_token and not self.token_manager.can_refresh:
            print("WARNING: CANVA_ACCESS_TOKEN not set.")
        self.timeout_seconds = timeout_seconds

    @property
    def access_token(self) -> str | None:
        return self.token_manager.access_token

    @property
    def headers(self) -> dict[str, str]:
        return self._build_headers(refresh_if_missing=True)

    def _build_headers(
        self,
        headers: Optional[dict[str, str]] = None,
        *,
        refresh_if_missing: bool = False,
    ) -> dict[str, str]:
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)

        if "Authorization" not in request_headers:
            access_token = self.token_manager.get_access_token(refresh_if_missing=refresh_if_missing)
            if access_token:
                request_headers["Authorization"] = f"Bearer {access_token}"
        return request_headers

    def _send_request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
        data: Optional[Any] = None,
        files: Optional[Any] = None,
        timeout_seconds: Optional[int] = None,
    ) -> requests.Response:
        try:
            return requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json,
                data=data,
                files=files,
                timeout=timeout_seconds or self.timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            handle_request_exception(exc, f"{method} {url}")

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
        data: Optional[Any] = None,
        files: Optional[Any] = None,
        headers: Optional[dict[str, str]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> requests.Response:
        url = f"{self.BASE_URL}{endpoint}"
        request_headers = self._build_headers(headers)
        preemptively_refreshed = False

        if "Authorization" not in request_headers and self.token_manager.can_refresh:
            request_headers["Authorization"] = f"Bearer {self.token_manager.refresh_access_token()}"
            preemptively_refreshed = True

        response = self._send_request(
            method,
            url,
            headers=request_headers,
            params=params,
            json=json,
            data=data,
            files=files,
            timeout_seconds=timeout_seconds,
        )

        if (
            response.status_code in (401, 403)
            and self.token_manager.can_refresh
            and not preemptively_refreshed
        ):
            retry_headers = request_headers.copy()
            retry_headers["Authorization"] = f"Bearer {self.token_manager.refresh_access_token()}"
            response = self._send_request(
                method,
                url,
                headers=retry_headers,
                params=params,
                json=json,
                data=data,
                files=files,
                timeout_seconds=timeout_seconds,
            )

        if response.status_code >= 400:
            raise_for_http_error(response)
        return response

    def _get(self, endpoint, params=None):
        response = self._request("GET", endpoint, params=params)
        return response.json()

    def _post(self, endpoint, json=None, data=None, files=None, headers=None):
        request_headers = self._build_headers(headers).copy()
        if files:
            # Let requests handle Content-Type for multipart/form-data
            request_headers.pop("Content-Type", None)

        response = self._request(
            "POST",
            endpoint,
            json=json,
            data=data,
            files=files,
            headers=request_headers,
        )
        return response.json()

    def _patch(self, endpoint, json=None):
        response = self._request("PATCH", endpoint, json=json)
        return response.json()

    def _delete(self, endpoint):
        response = self._request("DELETE", endpoint)
        return response.status_code == 204
