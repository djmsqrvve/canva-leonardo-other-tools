import os
import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials

class YouTubeClient:
    """Helper class to interact with the YouTube Data API v3."""
    
    def __init__(self, credentials=None):
        self.credentials = credentials
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.youtube = None

    def auth(self):
        """Authorize the client."""
        if not self.credentials:
            print("ERROR: YouTube credentials required.")
            return False
        self.youtube = googleapiclient.discovery.build(
            self.api_service_name, self.api_version, credentials=self.credentials)
        return True

    def update_thumbnail(self, video_id, image_path):
        """Update a video thumbnail."""
        if not self.youtube: return False
        
        request = self.youtube.thumbnails().set(
            videoId=video_id,
            media_body=googleapiclient.http.MediaFileUpload(image_path)
        )
        response = request.execute()
        return response
