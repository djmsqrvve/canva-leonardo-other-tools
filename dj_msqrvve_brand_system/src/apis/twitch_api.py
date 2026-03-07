import os
import requests

class TwitchClient:
    """Helper class to interact with the Twitch API (via Helix)."""
    
    BASE_URL = "https://api.twitch.tv/helix"

    def __init__(self, client_id=None, access_token=None):
        self.client_id = client_id or os.environ.get("TWITCH_CLIENT_ID")
        self.access_token = access_token or os.environ.get("TWITCH_ACCESS_TOKEN")
        
        if not self.client_id or not self.access_token:
            print("WARNING: TWITCH_CLIENT_ID or TWITCH_ACCESS_TOKEN not set.")
            
        self.headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.access_token}"
        }

    def get_user_info(self, login_name):
        """Fetch user profile information."""
        url = f"{self.BASE_URL}/users?login={login_name}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def update_channel_info(self, broadcaster_id, title=None, game_id=None):
        """Update channel title or game category."""
        url = f"{self.BASE_URL}/channels?broadcaster_id={broadcaster_id}"
        payload = {}
        if title: payload["title"] = title
        if game_id: payload["game_id"] = game_id
        
        response = requests.patch(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.status_code == 204
