import os
import requests
import base64
import urllib.parse
import pkce
from flask import Flask, request, redirect

# --- OAuth Configuration ---
# You need to configure this exact URL in your Canva Developer Portal
# under Your Integrations -> Authentication -> Redirect URLs
REDIRECT_URI = "http://127.0.0.1:5000/oauth/callback"

# Scopes needed for our automation pipeline
SCOPES = "design:content:read design:meta:read design:content:write design:meta:write asset:read asset:write brandtemplate:read brandtemplate:meta:read profile:read"

def start_canva_auth_server(client_id, client_secret, env_file_path):
    """
    Spins up a temporary local Flask server to handle the Canva OAuth 2.0 flow with PKCE.
    """
    app = Flask(__name__)

    # 1. Generate PKCE verifier and challenge
    code_verifier, code_challenge = pkce.generate_pkce_pair()

    # 2. Generate the Authorization URL
    auth_url = "https://www.canva.com/api/oauth/authorize"
    
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "state": "state_12345", # Protect against CSRF
        "code_challenge": code_challenge,
        "code_challenge_method": "s256"
    }
    
    url_params = urllib.parse.urlencode(params)
    full_auth_url = f"{auth_url}?{url_params}"

    print("\n" + "="*60)
    print("ACTION REQUIRED: Open this URL in your browser to authorize:")
    print(full_auth_url)
    print("="*60 + "\n")

    @app.route('/oauth/callback')
    def callback():
        error = request.args.get('error')
        if error:
            return f"Error during authorization: {error}", 400

        code = request.args.get('code')
        if not code:
            return "No authorization code provided in the callback.", 400

        # 3. Exchange the code for an Access Token
        token_url = "https://api.canva.com/rest/v1/oauth/token"
        
        # Canva requires basic auth for the token exchange
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode('utf-8')
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier
        }

        try:
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            
            # 3. Save the token back to the .env file
            update_env_file(env_file_path, "CANVA_ACCESS_TOKEN", access_token)
            if refresh_token:
                update_env_file(env_file_path, "CANVA_REFRESH_TOKEN", refresh_token)
            
            # Shut down the server gracefully
            shutdown_func = request.environ.get('werkzeug.server.shutdown')
            if shutdown_func:
                shutdown_func()
                
            return "<h1>Authentication Successful!</h1><p>The CANVA_ACCESS_TOKEN has been saved to your .env file. You can close this window and return to your terminal.</p>"
            
        except requests.exceptions.RequestException as e:
            err_msg = e.response.text if e.response else str(e)
            return f"<h1>Error exchanging token</h1><p>{err_msg}</p>", 500

    print("Starting local server to catch the callback...")
    print("Ensure you have added 'http://127.0.0.1:5000/oauth/callback' to your Canva Integration's Redirect URLs.")
    # Run the server on port 5000
    app.run(host="127.0.0.1", port=5000)

def update_env_file(file_path, key, value):
    """Updates or adds a key-value pair in the .env file."""
    lines = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
    key_found = False
    with open(file_path, 'w') as f:
        for line in lines:
            if line.startswith(f"{key}="):
                f.write(f"{key}={value}\n")
                key_found = True
            else:
                f.write(line)
        if not key_found:
            f.write(f"{key}={value}\n")

if __name__ == "__main__":
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(env_path)
    
    client_id = os.environ.get("CANVA_CLIENT_ID")
    client_secret = os.environ.get("CANVA_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("ERROR: CANVA_CLIENT_ID and CANVA_CLIENT_SECRET must be set in the .env file.")
    else:
        start_canva_auth_server(client_id, client_secret, env_path)
