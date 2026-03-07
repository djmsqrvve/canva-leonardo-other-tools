import os
import requests

class DiscordClient:
    """Helper class to interact with Discord Webhooks or API."""
    
    def __init__(self, bot_token=None):
        self.bot_token = bot_token or os.environ.get("DISCORD_BOT_TOKEN")
        self.headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }

    def post_webhook(self, webhook_url, content, embeds=None):
        """Send a message via Discord Webhook."""
        payload = {"content": content}
        if embeds:
            payload["embeds"] = embeds
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        return response.status_code == 204

    def update_guild_banner(self, guild_id, image_data):
        """Update Discord server banner (Requires Boosted Server)."""
        url = f"https://discord.com/api/v10/guilds/{guild_id}"
        payload = {"banner": image_data}
        response = requests.patch(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
