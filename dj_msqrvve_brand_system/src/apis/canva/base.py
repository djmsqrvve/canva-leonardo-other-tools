import os
from typing import Any, Optional

import requests

from lib.errors import handle_request_exception, raise_for_http_error

class CanvaBaseClient:
    """Base class for all Canva Connect API modules."""
    
    BASE_URL = "https://api.canva.com/rest/v1"

    def __init__(self, access_token=None, timeout_seconds: int = 30):
        self.access_token = access_token or os.environ.get("CANVA_ACCESS_TOKEN")
        if not self.access_token:
            print("WARNING: CANVA_ACCESS_TOKEN not set.")
        self.timeout_seconds = timeout_seconds
            
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

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
        request_headers = headers or self.headers
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=request_headers,
                params=params,
                json=json,
                data=data,
                files=files,
                timeout=timeout_seconds or self.timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            handle_request_exception(exc, f"{method} {url}")

        if response.status_code >= 400:
            raise_for_http_error(response)
        return response

    def _get(self, endpoint, params=None):
        response = self._request("GET", endpoint, params=params)
        return response.json()

    def _post(self, endpoint, json=None, data=None, files=None, headers=None):
        request_headers = (headers or self.headers).copy()
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
