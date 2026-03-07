import pytest
import os
import yaml
from unittest.mock import patch
from cli import generate_leonardo_asset, composite_in_canva, load_config

@pytest.fixture
def mock_config():
    return {
        "models": {
            "phoenix": "model_id_1"
        },
        "prompts": {
            "test_asset": {
                "model": "phoenix",
                "prompt": "A cool prompt",
                "width": 1024,
                "height": 1024
            }
        },
        "canva_templates": {
            "test_template": "canva_id_123"
        }
    }

def test_generate_leonardo_asset_missing_prompt(mock_config):
    with pytest.raises(ValueError, match="No prompt configuration found"):
        generate_leonardo_asset(mock_config, "non_existent_asset")

def test_generate_leonardo_asset_mocked_success(mock_config, capsys):
    # Currently cli.py mocks the API call natively
    url = generate_leonardo_asset(mock_config, "test_asset")
    assert url == "https://mock.leonardo.ai/generated_test_asset.png"
    captured = capsys.readouterr()
    assert "Generating test_asset" in captured.out

def test_composite_in_canva_no_template(mock_config, capsys):
    result = composite_in_canva(mock_config, "non_existent_template", "http://image.png")
    assert result is None
    captured = capsys.readouterr()
    assert "Skipping Canva step" in captured.out

def test_composite_in_canva_mocked_success(mock_config, capsys):
    # Currently cli.py mocks the API call natively
    result = composite_in_canva(mock_config, "test_template", "http://image.png")
    assert result == "mock_canva_design_id"
    captured = capsys.readouterr()
    assert "Compositing in Canva" in captured.out
