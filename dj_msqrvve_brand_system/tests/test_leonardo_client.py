import os
import pytest
import responses
from apis.leonardo_api import LeonardoClient

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("LEONARDO_API_KEY", "test_leonardo_key")

def test_init_no_key_raises_error():
    # Should raise error if no env var and no key passed
    with pytest.raises(ValueError):
        LeonardoClient()

def test_init_with_key():
    client = LeonardoClient(api_key="test_key")
    assert client.api_key == "test_key"
    assert "authorization" in client.headers
    assert client.headers["authorization"] == "Bearer test_key"

def test_init_with_env_var(mock_env):
    client = LeonardoClient()
    assert client.api_key == "test_leonardo_key"

@responses.activate
def test_generate_image(mock_env):
    client = LeonardoClient()
    
    responses.add(
        responses.POST,
        f"{client.BASE_URL}/generations",
        json={"sdGenerationJob": {"generationId": "test_gen_id"}},
        status=200
    )
    
    gen_id = client.generate_image("A test prompt", "test_model_id")
    
    assert gen_id == "test_gen_id"
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == f"{client.BASE_URL}/generations"

@responses.activate
def test_get_generation_result_complete(mock_env):
    client = LeonardoClient()
    
    responses.add(
        responses.GET,
        f"{client.BASE_URL}/generations/test_gen_id",
        json={
            "generations_by_pk": {
                "status": "COMPLETE",
                "generated_images": [{"url": "http://test.url/image1.png"}]
            }
        },
        status=200
    )
    
    urls = client.get_generation_result("test_gen_id")
    assert urls == ["http://test.url/image1.png"]

@responses.activate
def test_get_generation_result_timeout(mock_env):
    client = LeonardoClient()
    
    responses.add(
        responses.GET,
        f"{client.BASE_URL}/generations/test_gen_id",
        json={"generations_by_pk": {"status": "PENDING"}},
        status=200
    )
    
    # Should timeout because it stays pending
    with pytest.raises(TimeoutError):
        client.get_generation_result("test_gen_id", max_retries=2, wait_seconds=0.1)
