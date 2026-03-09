import os
from typing import Any, Optional

from .canva.assets import AssetsClient
from .canva.designs import DesignsClient
from .canva.autofill import AutofillClient
from .canva.exports import ExportsClient
from lib.errors import ApiResponseError
from lib.utils import extract_nested, poll_job

class CanvaClient:
    """
    Facade class for the Canva Connect API.
    Combines specialized modules for convenience while maintaining modularity.
    """
    def __init__(self, access_token=None):
        self.access_token = access_token or os.environ.get("CANVA_ACCESS_TOKEN")
        
        self.assets = AssetsClient(self.access_token)
        self.designs = DesignsClient(self.access_token)
        self.autofill = AutofillClient(self.access_token)
        self.exports = ExportsClient(self.access_token)
        
        # Shortcuts for common methods (backward compatibility)
        self.headers = self.assets.headers
        self.BASE_URL = self.assets.BASE_URL

    def _require_token(self) -> None:
        if not self.access_token:
            raise ValueError("Cannot call API without access token.")

    def _extract_status(self, payload: dict[str, Any]) -> Optional[str]:
        value = extract_nested(payload, ("job.status", "status", "autofill.status", "export.status"))
        return str(value) if value is not None else None

    def _extract_design_id(self, payload: dict[str, Any]) -> Optional[str]:
        return extract_nested(
            payload,
            (
                "job.result.design.id",
                "job.result.design_id",
                "design.id",
                "design_id",
            ),
        )

    def _extract_export_urls(self, payload: dict[str, Any]) -> list[str]:
        candidates: list[str] = []
        for path in (
            "job.result.urls",
            "job.result.files",
            "export.urls",
            "urls",
        ):
            value = extract_nested(payload, (path,))
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        candidates.append(item)
                    elif isinstance(item, dict):
                        url = item.get("url") or item.get("download_url")
                        if isinstance(url, str):
                            candidates.append(url)
        return candidates

    def get_or_create_shadowpunk_folder(self, folder_path: str = "Shadowpunk/Generations") -> str:
        self._require_token()
        return self.assets.get_or_create_folder_path(folder_path)

    def upload_asset(
        self,
        file_path: str,
        *,
        folder_id: Optional[str] = None,
        folder_path: Optional[str] = None,
    ) -> dict[str, Any]:
        self._require_token()
        resolved_folder_id = folder_id
        if folder_path and not resolved_folder_id:
            resolved_folder_id = self.assets.get_or_create_folder_path(folder_path)
        return self.assets.upload_asset(file_path, folder_id=resolved_folder_id)

    def autofill_template(self, template_id, data):
        """Proxy to AutofillClient."""
        self._require_token()
        response = self.autofill.start_autofill_job(template_id, data)
        job_id = response.get("job", {}).get("id")
        if not job_id:
            raise ApiResponseError("Canva autofill did not return a job ID.")
        return job_id

    def wait_for_autofill_job(self, job_id: str) -> dict[str, Any]:
        self._require_token()
        payload = poll_job(
            job_id,
            "canva-autofill",
            self.autofill.get_autofill_job_status,
            status_extractor=self._extract_status,
            success_statuses=("success", "complete", "completed", "done"),
            failure_statuses=("failed", "error", "canceled"),
            max_attempts=25,
            initial_delay_seconds=1.0,
            backoff_factor=1.5,
            max_delay_seconds=8.0,
        )
        return {"job_id": job_id, "design_id": self._extract_design_id(payload), "status_payload": payload}

    def export_design(self, design_id, format_type="png"):
        """Proxy to ExportsClient."""
        self._require_token()
        response = self.exports.start_export_job(design_id, format_type)
        job_id = response.get("job", {}).get("id")
        if not job_id:
            raise ApiResponseError("Canva export did not return a job ID.")
        return job_id

    def wait_for_export_job(self, job_id: str) -> dict[str, Any]:
        self._require_token()
        payload = poll_job(
            job_id,
            "canva-export",
            self.exports.get_export_job_status,
            status_extractor=self._extract_status,
            success_statuses=("success", "complete", "completed", "done"),
            failure_statuses=("failed", "error", "canceled"),
            max_attempts=25,
            initial_delay_seconds=1.0,
            backoff_factor=1.5,
            max_delay_seconds=8.0,
        )
        return {
            "job_id": job_id,
            "download_urls": self._extract_export_urls(payload),
            "status_payload": payload,
        }
