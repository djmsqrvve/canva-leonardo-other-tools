from pathlib import Path

import auth_server


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200
        self.text = ""

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_get_requested_scopes_can_include_autofill(monkeypatch):
    monkeypatch.delenv("CANVA_SCOPES", raising=False)
    monkeypatch.setenv("CANVA_INCLUDE_AUTOFILL_SCOPES", "1")

    scopes = auth_server.get_requested_scopes()
    assert "brandtemplate:meta:read" in scopes
    assert "brandtemplate:content:read" in scopes


def test_callback_rejects_invalid_oauth_state(tmp_path):
    env_path = tmp_path / ".env"
    app, _metadata = auth_server.create_canva_auth_app("client", "secret", str(env_path))
    client = app.test_client()

    response = client.get("/oauth/callback?code=abc123&state=wrong")
    assert response.status_code == 400
    assert b"Invalid OAuth state" in response.data


def test_callback_persists_access_and_refresh_tokens(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("", encoding="utf-8")
    recorded = {}

    def fake_post(url, headers, data, timeout):
        recorded["url"] = url
        recorded["headers"] = headers
        recorded["data"] = data
        recorded["timeout"] = timeout
        return DummyResponse({"access_token": "access_123", "refresh_token": "refresh_456"})

    app, metadata = auth_server.create_canva_auth_app(
        "client",
        "secret",
        str(env_path),
        request_post=fake_post,
    )
    client = app.test_client()

    response = client.get(f"/oauth/callback?code=abc123&state={metadata['state']}")
    assert response.status_code == 200
    assert recorded["url"] == auth_server.TOKEN_URL
    assert recorded["timeout"] == auth_server.TOKEN_TIMEOUT_SECONDS

    env_text = Path(env_path).read_text(encoding="utf-8")
    assert "CANVA_ACCESS_TOKEN=access_123" in env_text
    assert "CANVA_REFRESH_TOKEN=refresh_456" in env_text
