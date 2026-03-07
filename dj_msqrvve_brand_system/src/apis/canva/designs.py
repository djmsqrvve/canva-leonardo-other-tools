from .base import CanvaBaseClient

class DesignsClient(CanvaBaseClient):
    """Module for handling Canva design creation and metadata."""
    
    def create_design(self, title, design_type=None, width=None, height=None, asset_id=None):
        payload = {"title": title}
        if design_type:
            payload["design_type"] = {"type": design_type}
        if width and height:
            payload["width"] = width
            payload["height"] = height
        if asset_id:
            payload["asset_id"] = asset_id
            
        return self._post("/designs", json=payload)

    def get_design_details(self, design_id):
        return self._get(f"/designs/{design_id}")

    def get_brand_templates(self):
        return self._get("/brand-templates")
