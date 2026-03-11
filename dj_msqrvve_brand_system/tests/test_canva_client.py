import os
import pytest
import responses
from apis.canva_api import CanvaClient
from apis.canva.auth import TOKEN_URL
from lib.errors import ApiResponseError, AuthError
from responses.matchers import query_param_matcher


@pytest.fixture(autouse=True)
def clear_canva_env(monkeypatch):
    for key in (
        "CANVA_ACCESS_TOKEN",
        "CANVA_REFRESH_TOKEN",
        "CANVA_CLIENT_ID",
        "CANVA_CLIENT_SECRET",
    ):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("CANVA_ACCESS_TOKEN", "test_canva_token")

def test_init_with_key():
    client = CanvaClient(access_token="test_key")
    assert client.access_token == "test_key"
    assert client.headers["Authorization"] == "Bearer test_key"

def test_init_with_env_var(mock_env):
    client = CanvaClient()
    assert client.access_token == "test_canva_token"

def test_init_no_key_warning(capsys, monkeypatch):
    # Missing CANVA_ACCESS_TOKEN prints a warning
    monkeypatch.delenv("CANVA_ACCESS_TOKEN", raising=False)
    client = CanvaClient()
    assert client.access_token is None

@responses.activate
def test_autofill_template(mock_env):
    client = CanvaClient()
    
    responses.add(
        responses.POST,
        f"{client.BASE_URL}/autofills",
        json={"job": {"id": "test_job_id"}},
        status=200
    )
    
    job_id = client.autofill_template("template_123", {"Title": "Hello"})
    
    assert job_id == "test_job_id"
    assert len(responses.calls) == 1

def test_autofill_template_no_token(monkeypatch):
    monkeypatch.delenv("CANVA_ACCESS_TOKEN", raising=False)
    client = CanvaClient()
    with pytest.raises(ValueError, match="Cannot call API without access token"):
        client.autofill_template("template_123", {})

@responses.activate
def test_export_design(mock_env):
    client = CanvaClient()
    
    responses.add(
        responses.POST,
        f"{client.BASE_URL}/exports",
        json={"job": {"id": "export_job_id"}},
        status=200
    )
    
    job_id = client.export_design("design_123", "png")
    assert job_id == "export_job_id"


@responses.activate
def test_get_or_create_shadowpunk_folder(mock_env):
    client = CanvaClient()

    responses.add(
        responses.GET,
        f"{client.BASE_URL}/folders/root/items",
        json={"items": []},
        match=[query_param_matcher({"item_types": "folder"})],
        status=200,
    )
    responses.add(
        responses.POST,
        f"{client.BASE_URL}/folders",
        json={"folder": {"id": "folder_shadowpunk"}},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{client.BASE_URL}/folders/folder_shadowpunk/items",
        json={"items": []},
        match=[query_param_matcher({"item_types": "folder"})],
        status=200,
    )
    responses.add(
        responses.POST,
        f"{client.BASE_URL}/folders",
        json={"folder": {"id": "folder_generations"}},
        status=200,
    )

    folder_id = client.get_or_create_shadowpunk_folder()
    assert folder_id == "folder_generations"


@responses.activate
def test_upload_asset_happy_path(mock_env, tmp_path, monkeypatch):
    client = CanvaClient()
    file_path = tmp_path / "asset.png"
    file_path.write_bytes(b"test-bytes")

    responses.add(
        responses.POST,
        f"{client.BASE_URL}/asset-uploads",
        json={
            "job": {"id": "upload_job_1"},
            "upload_url": "https://upload.test/signed-url",
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{client.BASE_URL}/asset-uploads/upload_job_1",
        json={"job": {"status": "SUCCESS", "result": {"asset": {"id": "asset_123"}}}},
        status=200,
    )

    class DummyResponse:
        status_code = 200
        text = ""

    def fake_put(url, data, headers, timeout):
        assert url == "https://upload.test/signed-url"
        assert headers["Content-Type"] == "image/png"
        return DummyResponse()

    monkeypatch.setattr("apis.canva.assets.requests.put", fake_put)

    result = client.upload_asset(str(file_path), folder_id="folder_generations")
    assert result["asset_id"] == "asset_123"
    assert result["job_id"] == "upload_job_1"


def test_autofill_template_missing_job_id_raises(mock_env, monkeypatch):
    client = CanvaClient()

    class StubAutofill:
        @staticmethod
        def start_autofill_job(_template_id, _data):
            return {"job": {}}

    monkeypatch.setattr(client, "autofill", StubAutofill())

    with pytest.raises(ApiResponseError, match="autofill did not return a job ID"):
        client.autofill_template("template_123", {"Title": "Hello"})


def test_export_design_missing_job_id_raises(mock_env, monkeypatch):
    client = CanvaClient()

    class StubExports:
        @staticmethod
        def start_export_job(_design_id, _format_type):
            return {"job": {}}

    monkeypatch.setattr(client, "exports", StubExports())

    with pytest.raises(ApiResponseError, match="export did not return a job ID"):
        client.export_design("design_123", "png")


@responses.activate
def test_upload_asset_missing_job_id_raises(mock_env, tmp_path):
    client = CanvaClient()
    file_path = tmp_path / "asset.png"
    file_path.write_bytes(b"test-bytes")

    responses.add(
        responses.POST,
        f"{client.BASE_URL}/asset-uploads",
        json={"upload_url": "https://upload.test/signed-url"},
        status=200,
    )

    with pytest.raises(ApiResponseError, match="did not return a job ID"):
        client.upload_asset(str(file_path), folder_id="folder_generations")


@responses.activate
def test_upload_asset_http_error_raises(mock_env, tmp_path):
    client = CanvaClient()
    file_path = tmp_path / "asset.png"
    file_path.write_bytes(b"test-bytes")

    responses.add(
        responses.POST,
        f"{client.BASE_URL}/asset-uploads",
        json={"error": "bad request"},
        status=400,
    )

    with pytest.raises(ApiResponseError, match="400"):
        client.upload_asset(str(file_path), folder_id="folder_generations")


@responses.activate
def test_upload_asset_terminal_failed_status_raises(mock_env, tmp_path):
    client = CanvaClient()
    file_path = tmp_path / "asset.png"
    file_path.write_bytes(b"test-bytes")

    responses.add(
        responses.POST,
        f"{client.BASE_URL}/asset-uploads",
        json={"job": {"id": "upload_job_1"}},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{client.BASE_URL}/asset-uploads/upload_job_1",
        json={"job": {"status": "FAILED"}},
        status=200,
    )

    with pytest.raises(ApiResponseError, match="failed with status"):
        client.upload_asset(str(file_path), folder_id="folder_generations")


@responses.activate
def test_request_retries_after_refresh_and_persists_rotated_tokens(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "CANVA_ACCESS_TOKEN=expired_token\nCANVA_REFRESH_TOKEN=refresh_old\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CANVA_ACCESS_TOKEN", "expired_token")
    monkeypatch.setenv("CANVA_REFRESH_TOKEN", "refresh_old")
    monkeypatch.setenv("CANVA_CLIENT_ID", "client_123")
    monkeypatch.setenv("CANVA_CLIENT_SECRET", "secret_456")

    client = CanvaClient(env_file_path=str(env_path))

    responses.add(
        responses.GET,
        f"{client.BASE_URL}/folders/root/items",
        status=401,
        match=[query_param_matcher({"item_types": "folder"})],
    )
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"access_token": "fresh_access", "refresh_token": "refresh_new"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{client.BASE_URL}/folders/root/items",
        json={"items": []},
        status=200,
        match=[query_param_matcher({"item_types": "folder"})],
    )

    payload = client.assets.list_folder_items("root", item_types="folder")

    assert payload == {"items": []}
    assert client.access_token == "fresh_access"
    assert client.refresh_token == "refresh_new"
    assert os.environ["CANVA_ACCESS_TOKEN"] == "fresh_access"
    assert os.environ["CANVA_REFRESH_TOKEN"] == "refresh_new"

    env_text = env_path.read_text(encoding="utf-8")
    assert "CANVA_ACCESS_TOKEN=fresh_access" in env_text
    assert "CANVA_REFRESH_TOKEN=refresh_new" in env_text

    api_calls = [
        call.request.headers["Authorization"]
        for call in responses.calls
        if call.request.url.startswith(f"{client.BASE_URL}/folders/root/items")
    ]
    assert api_calls == ["Bearer expired_token", "Bearer fresh_access"]

    refresh_body = responses.calls[1].request.body
    if isinstance(refresh_body, bytes):
        refresh_body = refresh_body.decode("utf-8")
    assert "grant_type=refresh_token" in refresh_body
    assert "refresh_token=refresh_old" in refresh_body


@responses.activate
def test_request_refresh_failure_surfaces_auth_error(monkeypatch):
    monkeypatch.setenv("CANVA_ACCESS_TOKEN", "expired_token")
    monkeypatch.setenv("CANVA_REFRESH_TOKEN", "refresh_old")
    monkeypatch.setenv("CANVA_CLIENT_ID", "client_123")
    monkeypatch.setenv("CANVA_CLIENT_SECRET", "secret_456")

    client = CanvaClient()

    responses.add(
        responses.GET,
        f"{client.BASE_URL}/folders/root/items",
        status=401,
        match=[query_param_matcher({"item_types": "folder"})],
    )
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"error": "invalid_grant"},
        status=400,
    )

    with pytest.raises(AuthError, match="refresh failed"):
        client.assets.list_folder_items("root", item_types="folder")

    api_call_count = sum(
        1
        for call in responses.calls
        if call.request.url.startswith(f"{client.BASE_URL}/folders/root/items")
    )
    assert api_call_count == 1


@responses.activate
def test_request_without_refresh_token_raises_auth_error(monkeypatch):
    monkeypatch.delenv("CANVA_REFRESH_TOKEN", raising=False)
    monkeypatch.delenv("CANVA_CLIENT_ID", raising=False)
    monkeypatch.delenv("CANVA_CLIENT_SECRET", raising=False)

    client = CanvaClient(access_token="expired_token")

    responses.add(
        responses.GET,
        f"{client.BASE_URL}/folders/root/items",
        status=401,
        match=[query_param_matcher({"item_types": "folder"})],
    )

    with pytest.raises(AuthError):
        client.assets.list_folder_items("root", item_types="folder")

    assert len(responses.calls) == 1


@responses.activate
def test_refresh_without_rotated_refresh_token_keeps_existing_value(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "CANVA_ACCESS_TOKEN=expired_token\nCANVA_REFRESH_TOKEN=refresh_old\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CANVA_ACCESS_TOKEN", "expired_token")
    monkeypatch.setenv("CANVA_REFRESH_TOKEN", "refresh_old")
    monkeypatch.setenv("CANVA_CLIENT_ID", "client_123")
    monkeypatch.setenv("CANVA_CLIENT_SECRET", "secret_456")

    client = CanvaClient(env_file_path=str(env_path))

    responses.add(
        responses.GET,
        f"{client.BASE_URL}/folders/root/items",
        status=403,
        match=[query_param_matcher({"item_types": "folder"})],
    )
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"access_token": "fresh_access"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{client.BASE_URL}/folders/root/items",
        json={"items": []},
        status=200,
        match=[query_param_matcher({"item_types": "folder"})],
    )

    payload = client.assets.list_folder_items("root", item_types="folder")

    assert payload == {"items": []}
    assert client.access_token == "fresh_access"
    assert client.refresh_token == "refresh_old"
    assert os.environ["CANVA_REFRESH_TOKEN"] == "refresh_old"

    env_text = env_path.read_text(encoding="utf-8")
    assert "CANVA_ACCESS_TOKEN=fresh_access" in env_text
    assert env_text.count("CANVA_REFRESH_TOKEN=refresh_old") == 1
