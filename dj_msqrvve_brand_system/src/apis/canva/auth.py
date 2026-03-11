from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Callable

import requests

from lib.errors import ApiResponseError, AuthError, handle_request_exception, raise_for_http_error


TOKEN_URL = "https://api.canva.com/rest/v1/oauth/token"
TOKEN_TIMEOUT_SECONDS = 30
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


def resolve_env_file_path(env_file_path: str | os.PathLike[str] | None = None) -> Path | None:
    if env_file_path is not None:
        return Path(env_file_path)
    if DEFAULT_ENV_FILE.exists():
        return DEFAULT_ENV_FILE
    return None


def update_env_file(file_path: str | os.PathLike[str], key: str, value: str) -> None:
    path = Path(file_path)
    lines: list[str] = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

    key_found = False
    with path.open("w", encoding="utf-8") as file_obj:
        for line in lines:
            if line.startswith(f"{key}="):
                file_obj.write(f"{key}={value}\n")
                key_found = True
            else:
                file_obj.write(line)
        if not key_found:
            file_obj.write(f"{key}={value}\n")


def persist_canva_tokens(
    access_token: str,
    *,
    refresh_token: str | None = None,
    env_file_path: str | os.PathLike[str] | None = None,
) -> None:
    os.environ["CANVA_ACCESS_TOKEN"] = access_token
    if refresh_token:
        os.environ["CANVA_REFRESH_TOKEN"] = refresh_token

    resolved_env_file = resolve_env_file_path(env_file_path)
    if not resolved_env_file:
        return

    update_env_file(resolved_env_file, "CANVA_ACCESS_TOKEN", access_token)
    if refresh_token:
        update_env_file(resolved_env_file, "CANVA_REFRESH_TOKEN", refresh_token)


def build_basic_auth_header(client_id: str, client_secret: str) -> str:
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode("utf-8")
    return f"Basic {encoded_credentials}"


def exchange_oauth_token(
    *,
    grant_type: str,
    client_id: str,
    client_secret: str,
    data: dict[str, str],
    request_post: Callable[..., requests.Response] = requests.post,
    timeout_seconds: int = TOKEN_TIMEOUT_SECONDS,
) -> dict:
    headers = {
        "Authorization": build_basic_auth_header(client_id, client_secret),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {"grant_type": grant_type, **data}

    try:
        response = request_post(
            TOKEN_URL,
            headers=headers,
            data=payload,
            timeout=timeout_seconds,
        )
    except Exception as exc:  # noqa: BLE001
        handle_request_exception(exc, "POST Canva OAuth token")

    if response.status_code >= 400:
        raise_for_http_error(response)
    return response.json()


def refresh_canva_access_token(
    refresh_token: str,
    client_id: str,
    client_secret: str,
    *,
    request_post: Callable[..., requests.Response] = requests.post,
    timeout_seconds: int = TOKEN_TIMEOUT_SECONDS,
) -> dict:
    try:
        token_data = exchange_oauth_token(
            grant_type="refresh_token",
            client_id=client_id,
            client_secret=client_secret,
            data={"refresh_token": refresh_token},
            request_post=request_post,
            timeout_seconds=timeout_seconds,
        )
    except ApiResponseError as exc:
        raise AuthError(
            "Canva access token refresh failed.",
            status_code=exc.status_code,
            response_body=exc.response_body,
        ) from exc

    access_token = token_data.get("access_token")
    if not access_token:
        raise AuthError("Canva refresh response did not include an access token.")
    return token_data


class CanvaTokenManager:
    def __init__(
        self,
        *,
        access_token: str | None = None,
        refresh_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        env_file_path: str | os.PathLike[str] | None = None,
        timeout_seconds: int = TOKEN_TIMEOUT_SECONDS,
        request_post: Callable[..., requests.Response] = requests.post,
    ) -> None:
        self.access_token = access_token or os.environ.get("CANVA_ACCESS_TOKEN")
        self.refresh_token = refresh_token or os.environ.get("CANVA_REFRESH_TOKEN")
        self.client_id = client_id or os.environ.get("CANVA_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("CANVA_CLIENT_SECRET")
        self.env_file_path = resolve_env_file_path(env_file_path)
        self.timeout_seconds = timeout_seconds
        self.request_post = request_post

    @property
    def can_refresh(self) -> bool:
        return bool(self.refresh_token and self.client_id and self.client_secret)

    def get_access_token(self, *, refresh_if_missing: bool = True) -> str | None:
        if self.access_token:
            return self.access_token
        if refresh_if_missing and self.can_refresh:
            return self.refresh_access_token()
        return None

    def persist_tokens(self, access_token: str, *, refresh_token: str | None = None) -> str:
        persist_canva_tokens(
            access_token,
            refresh_token=refresh_token,
            env_file_path=self.env_file_path,
        )
        self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token
        return self.access_token

    def refresh_access_token(self) -> str:
        if not self.refresh_token:
            raise AuthError("Canva access token refresh requires CANVA_REFRESH_TOKEN.")
        if not self.client_id or not self.client_secret:
            raise AuthError(
                "Canva access token refresh requires CANVA_CLIENT_ID and CANVA_CLIENT_SECRET."
            )

        token_data = refresh_canva_access_token(
            self.refresh_token,
            self.client_id,
            self.client_secret,
            request_post=self.request_post,
            timeout_seconds=self.timeout_seconds,
        )
        new_token = self.persist_tokens(
            token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
        )
        print("Canva access token refreshed and saved to .env")
        return new_token
