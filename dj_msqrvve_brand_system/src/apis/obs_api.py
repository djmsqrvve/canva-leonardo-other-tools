import os
import obswsrc
from obswsrc import OBSWS
from obswsrc.requests import SetSceneItemPropertiesRequest

class OBSClient:
    """Helper class to interact with OBS via WebSocket."""
    
    def __init__(self, host="localhost", port=4455, password=None):
        self.host = host
        self.port = port
        self.password = password or os.environ.get("OBS_WS_PASSWORD")
        
    async def set_scene_item_visibility(self, scene_name, item_name, visible):
        """Toggle visibility of a scene item."""
        async with OBSWS(self.host, self.port, self.password) as obsws:
            props = SetSceneItemPropertiesRequest(
                scene_name=scene_name,
                item=item_name,
                visible=visible
            )
            await obsws.perform(props)
            print(f"OBS: Set {item_name} visibility to {visible} in scene {scene_name}.")
