from .base import CanvaBaseClient

class ExportsClient(CanvaBaseClient):
    """Module for handling design exports (PDF, PNG, MP4, etc.)."""
    
    def start_export_job(self, design_id, format_type):
        payload = {
            "design_id": design_id,
            "format": {"type": format_type}
        }
        return self._post("/exports", json=payload)

    def get_export_job_status(self, job_id):
        return self._get(f"/exports/{job_id}")

    def list_export_formats(self, design_id):
        return self._get(f"/designs/{design_id}/export-formats")
