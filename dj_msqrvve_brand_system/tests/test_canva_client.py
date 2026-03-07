import os
import pytest
import responses
from apis.canva_api import CanvaClient

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

def test_init_no_key_warning(capsys):
    # Missing CANVA_ACCESS_TOKEN prints a warning
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

def test_autofill_template_no_token():
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
