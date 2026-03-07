import os
import requests

class CanvaBaseClient:
    """Base class for all Canva Connect API modules."""
    
    BASE_URL = "https://api.canva.com/rest/v1"

    def __init__(self, access_token=None):
        self.access_token = access_token or os.environ.get("CANVA_ACCESS_TOKEN")
        if not self.access_token:
            print("WARNING: CANVA_ACCESS_TOKEN not set.")
            
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def _get(self, endpoint, params=None):
        response = requests.get(f"{self.BASE_URL}{endpoint}", headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint, json=None, data=None, files=None):
        headers = self.headers.copy()
        if files:
            # Let requests handle Content-Type for multipart/form-data
            del headers["Content-Type"]
            
        response = requests.post(f"{self.BASE_URL}{endpoint}", headers=headers, json=json, data=data, files=files)
        response.raise_for_status()
        return response.json()

    def _patch(self, endpoint, json=None):
        response = requests.patch(f"{self.BASE_URL}{endpoint}", headers=self.headers, json=json)
        response.raise_for_status()
        return response.json()

    def _delete(self, endpoint):
        response = requests.delete(f"{self.BASE_URL}{endpoint}", headers=self.headers)
        response.raise_for_status()
        return response.status_code == 204
