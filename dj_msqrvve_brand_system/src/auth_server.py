from __future__ import annotations

import os
import secrets
import urllib.parse
from typing import Callable

import pkce
import requests
from flask import Flask, request

from apis.canva.auth import (
    TOKEN_TIMEOUT_SECONDS,
    TOKEN_URL,
    exchange_oauth_token,
    persist_canva_tokens,
)
from lib.errors import ApiResponseError

# You need to configure this exact URL in the Canva Developer Portal
# under Your Integrations -> Authentication -> Redirect URLs.
REDIRECT_URI = "http://127.0.0.1:5000/oauth/callback"
AUTH_URL = "https://www.canva.com/api/oauth/authorize"

DEFAULT_SCOPES = [
    "design:content:read",
    "design:content:write",
    "design:meta:read",
    "asset:read",
    "asset:write",
    "folder:read",
    "folder:write",
    "profile:read",
]

AUTOFILL_SCOPES = [
    "brandtemplate:meta:read",
    "brandtemplate:content:read",
]


def get_requested_scopes() -> str:
    """
    Resolve requested scopes for OAuth.

    Priority:
    1) CANVA_SCOPES env var (space-delimited, explicit override)
    2) Defaults + optional brand-template scopes when CANVA_INCLUDE_AUTOFILL_SCOPES=1
    """
    explicit_scopes = os.environ.get("CANVA_SCOPES", "").strip()
    if explicit_scopes:
        return explicit_scopes

    include_autofill = os.environ.get("CANVA_INCLUDE_AUTOFILL_SCOPES", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    scopes = list(DEFAULT_SCOPES)
    if include_autofill:
        scopes.extend(AUTOFILL_SCOPES)
    return " ".join(scopes)


def build_auth_url(client_id: str, requested_scopes: str, code_challenge: str, state: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": requested_scopes,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "s256",
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"


def create_canva_auth_app(
    client_id: str,
    client_secret: str,
    env_file_path: str,
    *,
    request_post: Callable[..., requests.Response] = requests.post,
):
    """
    Build the local OAuth app and return it with the authorization URL.

    The returned metadata makes the flow testable without booting a real server.
    """
    app = Flask(__name__)
    code_verifier, code_challenge = pkce.generate_pkce_pair()
    requested_scopes = get_requested_scopes()
    oauth_state = secrets.token_urlsafe(24)
    full_auth_url = build_auth_url(client_id, requested_scopes, code_challenge, oauth_state)

    @app.route("/oauth/callback")
    def callback():
        error = request.args.get("error")
        if error:
            return f"Error during authorization: {error}", 400

        returned_state = request.args.get("state")
        if not returned_state or returned_state != oauth_state:
            return "Invalid OAuth state returned by Canva.", 400

        code = request.args.get("code")
        if not code:
            return "No authorization code provided in the callback.", 400

        try:
            token_data = exchange_oauth_token(
                grant_type="authorization_code",
                client_id=client_id,
                client_secret=client_secret,
                data={
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                    "code_verifier": code_verifier,
                },
                request_post=request_post,
                timeout_seconds=TOKEN_TIMEOUT_SECONDS,
            )

            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            if not access_token:
                return "<h1>Error exchanging token</h1><p>No access token returned.</p>", 500

            persist_canva_tokens(
                access_token,
                refresh_token=refresh_token,
                env_file_path=env_file_path,
            )

            shutdown_func = request.environ.get("werkzeug.server.shutdown")
            if shutdown_func:
                shutdown_func()

            return (
                "<h1>Authentication Successful!</h1>"
                "<p>The CANVA_ACCESS_TOKEN has been saved to your .env file. "
                "If Canva returned a refresh token, it was saved as CANVA_REFRESH_TOKEN.</p>"
            )
        except ApiResponseError as exc:
            err_msg = exc.response_body or str(exc)
            return f"<h1>Error exchanging token</h1><p>{err_msg}</p>", 500

    return app, {"auth_url": full_auth_url, "requested_scopes": requested_scopes, "state": oauth_state}


def start_canva_auth_server(client_id: str, client_secret: str, env_file_path: str):
    """Spin up a temporary local Flask server to handle the Canva OAuth 2.0 flow."""
    app, metadata = create_canva_auth_app(client_id, client_secret, env_file_path)

    print("\n" + "=" * 60)
    print("Requested scopes:")
    print(metadata["requested_scopes"])
    print("-" * 60)
    print("ACTION REQUIRED: Open this URL in your browser to authorize:")
    print(metadata["auth_url"])
    print("=" * 60 + "\n")

    print("Starting local server to catch the callback...")
    print("Ensure the redirect URL below is configured in your Canva integration:")
    print(REDIRECT_URI)
    print("Refresh tokens are saved when Canva returns them.")
    app.run(host="127.0.0.1", port=5000)


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
