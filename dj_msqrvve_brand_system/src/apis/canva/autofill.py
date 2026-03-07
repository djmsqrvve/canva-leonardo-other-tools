from .base import CanvaBaseClient

class AutofillClient(CanvaBaseClient):
    """Module for handling Canva design autofills from templates."""
    
    def start_autofill_job(self, brand_template_id, data, title=None):
        payload = {
            "brand_template_id": brand_template_id,
            "data": data
        }
        if title:
            payload["title"] = title
            
        return self._post("/autofills", json=payload)

    def get_autofill_job_status(self, job_id):
        return self._get(f"/autofills/{job_id}")
