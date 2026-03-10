import os
from typing import Any, Optional

import requests

from lib.errors import ApiResponseError, handle_request_exception, raise_for_http_error
from lib.utils import poll_job

class LeonardoClient:
    """Helper class to interact with the Leonardo.Ai API."""
    
    BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("LEONARDO_API_KEY")
        if not self.api_key:
            raise ValueError("LEONARDO_API_KEY environment variable not set.")
        self.timeout_seconds = 30
        
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.api_key}"
        }

    def _request(self, method: str, endpoint: str, *, json: Optional[dict[str, Any]] = None):
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                json=json,
                headers=self.headers,
                timeout=self.timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            handle_request_exception(exc, f"{method} {url}")
        if response.status_code >= 400:
            raise_for_http_error(response)
        return response.json()

    def _extract_generation_status(self, payload: dict[str, Any]) -> Optional[str]:
        status = payload.get("generations_by_pk", {}).get("status")
        return str(status) if status is not None else None

    def get_generation_details(self, generation_id: str) -> dict[str, Any]:
        return self._request("GET", f"/generations/{generation_id}")

    def generate_image(self, prompt, model_id, width=1024, height=1024, alchemy=True, num_images=1):
        """Triggers an image generation job."""
        payload = {
            "prompt": prompt,
            "modelId": model_id,
            "width": width,
            "height": height,
            "alchemy": alchemy,
            "num_images": num_images
        }

        data = self._request("POST", "/generations", json=payload)
        
        # Return the generation ID to poll for results
        return data.get("sdGenerationJob", {}).get("generationId")

    def get_generation_result(self, generation_id, max_retries=10, wait_seconds=5):
        """Polls the API for the result of a generation job."""
        payload = poll_job(
            generation_id,
            "leonardo-generation",
            self.get_generation_details,
            status_extractor=self._extract_generation_status,
            success_statuses=("complete",),
            failure_statuses=("failed",),
            max_attempts=max_retries,
            initial_delay_seconds=wait_seconds,
            backoff_factor=1.0,
            max_delay_seconds=wait_seconds,
        )
        images = payload.get("generations_by_pk", {}).get("generated_images", [])
        urls = [img.get("url") for img in images if img.get("url")]
        return {"generation_id": generation_id, "urls": urls, "status_payload": payload}

    def generate_and_wait(self, prompt, model_id, return_metadata=False, **kwargs):
        """Convenience method to trigger generation and wait for the result."""
        print(f"Triggering generation for prompt: '{prompt[:50]}...'")
        generation_id = self.generate_image(prompt, model_id, **kwargs)
        if not generation_id:
            raise ApiResponseError(f"Failed to get generation ID from response (got {generation_id!r})")
        
        print(f"Waiting for generation {generation_id} to complete...")
        result = self.get_generation_result(generation_id)
        if return_metadata:
            return result
        return result["urls"]
