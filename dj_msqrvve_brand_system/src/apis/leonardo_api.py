import os
import requests
import time

class LeonardoClient:
    """Helper class to interact with the Leonardo.Ai API."""
    
    BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("LEONARDO_API_KEY")
        if not self.api_key:
            raise ValueError("LEONARDO_API_KEY environment variable not set.")
        
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.api_key}"
        }

    def generate_image(self, prompt, model_id, width=1024, height=1024, alchemy=True, num_images=1):
        """Triggers an image generation job."""
        url = f"{self.BASE_URL}/generations"
        payload = {
            "prompt": prompt,
            "modelId": model_id,
            "width": width,
            "height": height,
            "alchemy": alchemy,
            "num_images": num_images
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        
        # Return the generation ID to poll for results
        return data.get("sdGenerationJob", {}).get("generationId")

    def get_generation_result(self, generation_id, max_retries=10, wait_seconds=5):
        """Polls the API for the result of a generation job."""
        url = f"{self.BASE_URL}/generations/{generation_id}"
        
        for _ in range(max_retries):
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            status = data.get("generations_by_pk", {}).get("status")
            if status == "COMPLETE":
                # Return list of generated image URLs
                images = data.get("generations_by_pk", {}).get("generated_images", [])
                return [img.get("url") for img in images]
            elif status == "FAILED":
                raise Exception(f"Generation job {generation_id} failed.")
            
            # Wait before polling again
            time.sleep(wait_seconds)
            
        raise TimeoutError(f"Generation job {generation_id} timed out after {max_retries * wait_seconds} seconds.")

    def generate_and_wait(self, prompt, model_id, **kwargs):
        """Convenience method to trigger generation and wait for the result."""
        print(f"Triggering generation for prompt: '{prompt[:50]}...'")
        generation_id = self.generate_image(prompt, model_id, **kwargs)
        if not generation_id:
            raise Exception("Failed to get generation ID from response.")
        
        print(f"Waiting for generation {generation_id} to complete...")
        urls = self.get_generation_result(generation_id)
        return urls
