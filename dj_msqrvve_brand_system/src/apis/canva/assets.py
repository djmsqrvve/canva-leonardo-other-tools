from .base import CanvaBaseClient
import os

class AssetsClient(CanvaBaseClient):
    """Module for handling Canva assets and folders."""
    
    def list_folder_items(self, folder_id="root", item_types=None):
        params = {}
        if item_types:
            params["item_types"] = item_types
        return self._get(f"/folders/{folder_id}/items", params=params)

    def create_folder(self, name, parent_id="root"):
        payload = {"name": name, "parent_id": parent_id}
        return self._post("/folders", json=payload)

    def upload_asset(self, file_path):
        """Starts an asynchronous asset upload."""
        file_name = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            # Canva requires the asset metadata to be in a X-Canva-Asset-Upload-Metadata header
            # and the file to be in the body.
            # (Note: This is based on typical Connect API upload patterns.)
            # For simplicity, we assume the API handles multipart for now or expects a certain header.
            # The official Docs use a multi-step job for large uploads.
            
            # Placeholder for actual Canva upload logic (which involves a Job ID)
            # return self._post("/asset-uploads", files={'file': f})
            pass

    def get_asset_details(self, asset_id):
        return self._get(f"/assets/{asset_id}")
