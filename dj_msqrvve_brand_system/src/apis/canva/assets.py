import base64
import json
import mimetypes
import os
from typing import Any, Optional

import requests

from lib.errors import ApiResponseError, handle_request_exception
from lib.utils import extract_nested, poll_job

from .base import CanvaBaseClient

class AssetsClient(CanvaBaseClient):
    """Module for handling Canva assets and folders."""
    
    def list_folder_items(self, folder_id="root", item_types=None):
        params = {}
        if item_types:
            params["item_types"] = item_types
        return self._get(f"/folders/{folder_id}/items", params=params)

    def create_folder(self, name, parent_id="root"):
        payload = {"name": name, "parent_folder_id": parent_id}
        return self._post("/folders", json=payload)

    def _extract_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("items", "folder_items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict) and isinstance(value.get("items"), list):
                return [item for item in value["items"] if isinstance(item, dict)]
        return []

    def _extract_folder_id(self, payload: dict[str, Any]) -> Optional[str]:
        return extract_nested(
            payload,
            (
                "folder.id",
                "data.folder.id",
                "id",
            ),
        )

    def _extract_job_id(self, payload: dict[str, Any]) -> Optional[str]:
        return extract_nested(payload, ("job.id", "asset_upload.id", "id"))

    def _extract_upload_url(self, payload: dict[str, Any]) -> Optional[str]:
        return extract_nested(
            payload,
            (
                "upload_url",
                "asset_upload.upload_url",
                "job.upload_url",
                "job.result.upload_url",
            ),
        )

    def _extract_asset_id(self, payload: dict[str, Any]) -> Optional[str]:
        return extract_nested(
            payload,
            (
                "job.asset.id",
                "asset.id",
                "job.result.asset.id",
                "job.result.asset_id",
                "asset_id",
                "result.asset.id",
            ),
        )

    def _extract_job_status(self, payload: dict[str, Any]) -> Optional[str]:
        value = extract_nested(
            payload,
            ("job.status", "status", "asset_upload.status", "job.result.status"),
        )
        if value is None:
            return None
        return str(value)

    def _upload_binary(self, upload_url: str, file_path: str, mime_type: str) -> None:
        headers = {"Content-Type": mime_type}
        try:
            with open(file_path, "rb") as file_obj:
                response = requests.put(
                    upload_url,
                    data=file_obj,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )
        except Exception as exc:  # noqa: BLE001
            handle_request_exception(exc, "upload binary to Canva signed URL")

        if response.status_code >= 400:
            raise ApiResponseError(
                f"Signed upload failed with status {response.status_code}",
                status_code=response.status_code,
                response_body=response.text,
            )

    def get_asset_upload_job_status(self, job_id: str):
        return self._get(f"/asset-uploads/{job_id}")

    def get_or_create_folder_path(self, folder_path: str, parent_id: str = "root") -> str:
        """Resolve a folder path like 'Shadowpunk/Generations' and create missing segments."""
        current_parent = parent_id
        for segment in [item.strip() for item in folder_path.split("/") if item.strip()]:
            response = self.list_folder_items(current_parent, item_types="folder")
            existing_folder_id = None
            for item in self._extract_items(response):
                item_type = (item.get("type") or item.get("item_type") or "").lower()
                inner = item.get("folder", {}) if "folder" in item_type else item
                name = inner.get("name") or item.get("name")
                folder_id = inner.get("id") or item.get("id")
                if name == segment and folder_id:
                    existing_folder_id = folder_id
                    break

            if existing_folder_id:
                current_parent = existing_folder_id
                continue

            created = self.create_folder(segment, parent_id=current_parent)
            created_id = self._extract_folder_id(created)
            if not created_id:
                raise ApiResponseError(f"Could not determine ID for created folder '{segment}'")
            current_parent = created_id

        return current_parent

    def get_or_create_shadowpunk_folder(self) -> str:
        return self.get_or_create_folder_path("Shadowpunk/Generations")

    def upload_asset(
        self,
        file_path: str,
        *,
        folder_id: Optional[str] = None,
        file_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """Upload a file to Canva via binary POST with metadata header."""
        resolved_name = file_name or os.path.basename(file_path)
        metadata: dict[str, str] = {
            "name_base64": base64.b64encode(resolved_name.encode()).decode(),
        }
        if folder_id:
            metadata["parent_folder_id"] = folder_id

        url = f"{self.BASE_URL}/asset-uploads"
        request_headers = self._build_headers(refresh_if_missing=True)
        request_headers["Content-Type"] = "application/octet-stream"
        request_headers["Asset-Upload-Metadata"] = json.dumps(metadata)

        with open(file_path, "rb") as f:
            file_data = f.read()

        try:
            response = self._send_request(
                "POST", url, headers=request_headers, data=file_data, timeout_seconds=60,
            )
        except Exception as exc:
            handle_request_exception(exc, "upload asset to Canva")

        if response.status_code >= 400:
            from lib.errors import raise_for_http_error
            raise_for_http_error(response)

        init_response = response.json()
        job_id = self._extract_job_id(init_response)
        if not job_id:
            raise ApiResponseError("Canva upload did not return a job ID.")

        completion_payload = poll_job(
            job_id,
            "canva-asset-upload",
            self.get_asset_upload_job_status,
            status_extractor=self._extract_job_status,
            success_statuses=("success", "complete", "completed", "done"),
            failure_statuses=("failed", "error", "canceled"),
            max_attempts=20,
            initial_delay_seconds=1.0,
            backoff_factor=1.5,
            max_delay_seconds=8.0,
        )

        asset_id = self._extract_asset_id(completion_payload)
        if not asset_id:
            raise ApiResponseError(
                "Upload finished without asset ID.",
                response_body=json.dumps(completion_payload),
            )

        return {
            "job_id": job_id,
            "asset_id": asset_id,
            "folder_id": folder_id,
            "file_name": resolved_name,
            "mime_type": mimetypes.guess_type(resolved_name)[0] or "application/octet-stream",
            "status_payload": completion_payload,
        }

    def get_asset_details(self, asset_id):
        return self._get(f"/assets/{asset_id}")
