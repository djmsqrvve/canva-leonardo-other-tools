import json
from pathlib import Path

import pytest

import main as main_module


def _config():
    return {
        "models": {"phoenix": "model_123"},
        "prompts": {
            "social_banner_bg": {
                "model": "phoenix",
                "prompt": "hello world",
                "width": 1024,
                "height": 1024,
                "alchemy": True,
            }
        },
        "canva_templates": {"social_banner_bg": "template_123"},
    }


def test_parser_supports_new_generate_api_flags():
    parser = main_module.create_parser()
    args = parser.parse_args(
        [
            "generate-api",
            "social_banner_bg",
            "--sync",
            "--autofill",
            "--export",
            "png",
            "--canva-folder",
            "Shadowpunk/Generations",
        ]
    )
    assert args.sync is True
    assert args.autofill is True
    assert args.export_format == "png"
    assert args.canva_folder == "Shadowpunk/Generations"


def test_generate_api_export_requires_autofill():
    parser = main_module.create_parser()
    args = parser.parse_args(["generate-api", "social_banner_bg", "--export", "png"])
    with pytest.raises(ValueError, match="--export requires --autofill"):
        main_module.run_generate_api(args, _config())


def test_generate_api_sync_uploads_and_writes_ledger(monkeypatch, tmp_path):
    leo_instances = []
    canva_instances = []

    class StubLeoClient:
        def __init__(self):
            leo_instances.append(self)

        def generate_and_wait(self, **kwargs):
            return {
                "generation_id": "gen_1",
                "urls": ["https://example.com/image.png"],
                "status_payload": {"ok": True},
            }

    class StubCanvaClient:
        def __init__(self):
            self.upload_calls = 0
            canva_instances.append(self)

        def get_or_create_shadowpunk_folder(self, folder_path):
            assert folder_path == "Shadowpunk/Generations"
            return "folder_1"

        def upload_asset(self, file_path, folder_id=None, folder_path=None):
            self.upload_calls += 1
            assert Path(file_path).exists()
            assert folder_id == "folder_1"
            return {"asset_id": "asset_1", "job_id": "job_1"}

    def fake_download(url, output_path, timeout_seconds=60):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"fake")

    monkeypatch.setattr(main_module, "LeonardoClient", StubLeoClient)
    monkeypatch.setattr(main_module, "CanvaClient", StubCanvaClient)
    monkeypatch.setattr(main_module, "download_to_file", fake_download)
    monkeypatch.setattr(main_module, "DEFAULT_OUTPUT_ROOT", tmp_path)

    parser = main_module.create_parser()
    args = parser.parse_args(["generate-api", "social_banner_bg", "--sync"])
    code = main_module.run_generate_api(args, _config())

    assert code == 0
    assert leo_instances
    assert canva_instances[0].upload_calls == 1

    ledger_file = tmp_path / "ledger.jsonl"
    assert ledger_file.exists()
    ledger_text = ledger_file.read_text(encoding="utf-8")
    assert '"stage": "sync"' in ledger_text
    assert '"status": "success"' in ledger_text


def test_generate_api_autofill_and_export(monkeypatch, tmp_path):
    class StubLeoClient:
        def generate_and_wait(self, **kwargs):
            return {
                "generation_id": "gen_1",
                "urls": ["https://example.com/image.png"],
                "status_payload": {"ok": True},
            }

    class StubCanvaClient:
        def get_or_create_shadowpunk_folder(self, folder_path):
            return "folder_1"

        def upload_asset(self, file_path, folder_id=None, folder_path=None):
            return {"asset_id": "asset_1", "job_id": "job_1"}

        def autofill_template(self, template_id, data):
            assert template_id == "template_123"
            return "autofill_1"

        def wait_for_autofill_job(self, job_id):
            assert job_id == "autofill_1"
            return {"job_id": job_id, "design_id": "design_1"}

        def export_design(self, design_id, format_type="png"):
            assert design_id == "design_1"
            assert format_type == "png"
            return "export_1"

        def wait_for_export_job(self, job_id):
            assert job_id == "export_1"
            return {"job_id": job_id, "download_urls": ["https://example.com/export.png"]}

    def fake_download(url, output_path, timeout_seconds=60):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"fake")

    monkeypatch.setattr(main_module, "LeonardoClient", StubLeoClient)
    monkeypatch.setattr(main_module, "CanvaClient", StubCanvaClient)
    monkeypatch.setattr(main_module, "download_to_file", fake_download)
    monkeypatch.setattr(main_module, "DEFAULT_OUTPUT_ROOT", tmp_path)

    parser = main_module.create_parser()
    args = parser.parse_args(
        [
            "generate-api",
            "social_banner_bg",
            "--autofill",
            "--export",
            "png",
        ]
    )

    code = main_module.run_generate_api(args, _config())
    assert code == 0

    ledger_file = tmp_path / "ledger.jsonl"
    assert ledger_file.exists()
    entries = [json.loads(line) for line in ledger_file.read_text(encoding="utf-8").splitlines() if line]
    assert any(entry["stage"] == "autofill" and entry["status"] == "success" for entry in entries)
    assert any(entry["stage"] == "export" and entry["status"] == "success" for entry in entries)
