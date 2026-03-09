import os
import requests
import yaml
from dotenv import load_dotenv
from apis.leonardo_api import LeonardoClient
from apis.canva_api import CanvaClient

def load_environment():
    """Loads environment variables from the .env file."""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(env_path)

def test_api_health():
    """Simple health check for both APIs using the saved credentials."""
    load_environment()
    
    print("\n" + "="*40)
    print("--- API HEALTH CHECK ---")
    print("="*40)

    # 1. Leonardo.Ai Health Check
    leo_key = os.environ.get("LEONARDO_API_KEY")
    if leo_key:
        try:
            client = LeonardoClient(leo_key)
            # Fetch user info as a simple check
            response = requests.get(
                f"{client.BASE_URL}/me",
                headers=client.headers,
                timeout=30,
            )
            if response.ok:
                print("✅ Leonardo.Ai: Authentication Successful!")
            else:
                print(f"❌ Leonardo.Ai: Authentication Failed ({response.status_code})")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Leonardo.Ai: Error - {str(e)}")
    else:
        print("⚠️ Leonardo.Ai: LEONARDO_API_KEY not found in .env")

    # 2. Canva Connect API Health Check
    canva_token = os.environ.get("CANVA_ACCESS_TOKEN")
    canva_refresh = os.environ.get("CANVA_REFRESH_TOKEN")
    if canva_token or canva_refresh:
        try:
            client = CanvaClient(canva_token)
            user_data = client.get_current_user()
            if user_data:
                print("✅ Canva Connect: Authentication Successful!")
                print(f"   Connected as: {user_data.get('user', {}).get('display_name', 'Unknown')}")
        except Exception as e:
            print(f"❌ Canva Connect: Error - {str(e)}")
    else:
        print("⚠️ Canva Connect: CANVA_ACCESS_TOKEN or CANVA_REFRESH_TOKEN not found in .env")

    print("="*40 + "\n")

if __name__ == "__main__":
    test_api_health()
