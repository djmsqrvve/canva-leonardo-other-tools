import os
import pytest
import responses
from apis.canva_api import CanvaClient
from responses.matchers import query_param_matcher

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
