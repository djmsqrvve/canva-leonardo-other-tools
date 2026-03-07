import os
from .canva.assets import AssetsClient
from .canva.designs import DesignsClient
from .canva.autofill import AutofillClient
from .canva.exports import ExportsClient

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

    def autofill_template(self, template_id, data):
        """Proxy to AutofillClient."""
        if not self.access_token:
            raise ValueError("Cannot call API without access token.")
        response = self.autofill.start_autofill_job(template_id, data)
        return response.get("job", {}).get("id")

    def export_design(self, design_id, format_type="png"):
        """Proxy to ExportsClient."""
        if not self.access_token:
            raise ValueError("Cannot call API without access token.")
        response = self.exports.start_export_job(design_id, format_type)
        return response.get("job", {}).get("id")
