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


def _read_ledger(ledger_file: Path) -> list[dict]:
    return [json.loads(line) for line in ledger_file.read_text(encoding="utf-8").splitlines() if line]


def _assert_stage_failed(entries: list[dict], stage: str):
    assert any(entry["stage"] == stage and entry["status"] == "started" for entry in entries)
    assert any(entry["stage"] == stage and entry["status"] == "failed" for entry in entries)


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


def test_create_leonardo_browser_surfaces_optional_dependency_error(monkeypatch):
    def fake_import(_module_name):
        exc = ModuleNotFoundError("No module named 'selenium'")
        exc.name = "selenium"
        raise exc

    monkeypatch.setattr(main_module, "import_module", fake_import)

    with pytest.raises(main_module.OptionalDependencyError, match="requirements-browser.txt"):
        main_module.create_leonardo_browser(headless=True)


def test_load_prompts_merges_local_template_overrides(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "prompts.yaml").write_text(
        (
            "models: {}\n"
            "prompts: {}\n"
            "canva_templates:\n"
            "  social_banner_bg: TEMPLATE_ID_HERE\n"
            "  bevy_skybox: base_template_123\n"
        ),
        encoding="utf-8",
    )
    (config_dir / "prompts.local.yaml").write_text(
        "canva_templates:\n  social_banner_bg: private_template_456\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(main_module, "PROJECT_ROOT", tmp_path)

    config = main_module.load_prompts()

    assert config["canva_templates"]["social_banner_bg"] == "private_template_456"
    assert config["canva_templates"]["bevy_skybox"] == "base_template_123"


def test_load_prompts_rejects_invalid_local_template_override(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "prompts.yaml").write_text("models: {}\nprompts: {}\n", encoding="utf-8")
    (config_dir / "prompts.local.yaml").write_text("canva_templates: []\n", encoding="utf-8")

    monkeypatch.setattr(main_module, "PROJECT_ROOT", tmp_path)

    with pytest.raises(main_module.ConfigurationError, match="must define canva_templates as a mapping"):
        main_module.load_prompts()


def test_resolve_canva_template_id_rejects_missing_mapping():
    with pytest.raises(main_module.ConfigurationError, match="No Canva template ID configured"):
        main_module.resolve_canva_template_id({"canva_templates": {}}, "social_banner_bg")


def test_resolve_canva_template_id_rejects_placeholder_mapping():
    with pytest.raises(main_module.ConfigurationError, match="prompts.local.yaml"):
        main_module.resolve_canva_template_id(
            {"canva_templates": {"social_banner_bg": "TEMPLATE_ID_HERE"}},
            "social_banner_bg",
        )


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
    entries = _read_ledger(ledger_file)
    assert any(entry["stage"] == "autofill" and entry["status"] == "success" for entry in entries)
    assert any(entry["stage"] == "export" and entry["status"] == "success" for entry in entries)


def test_generate_api_idempotent_resume_skips_completed_stages(monkeypatch, tmp_path):
    call_counts = {
        "generation": 0,
        "download": 0,
        "upload": 0,
    }

    class StubLeoClient:
        def generate_and_wait(self, **kwargs):
            call_counts["generation"] += 1
            return {
                "generation_id": "gen_1",
                "urls": ["https://example.com/image.png"],
                "status_payload": {"ok": True},
            }

    class StubCanvaClient:
        def get_or_create_shadowpunk_folder(self, folder_path):
            return "folder_1"

        def upload_asset(self, file_path, folder_id=None, folder_path=None):
            call_counts["upload"] += 1
            return {"asset_id": "asset_1", "job_id": "job_1"}

    def fake_download(url, output_path, timeout_seconds=60):
        call_counts["download"] += 1
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"fake")

    monkeypatch.setattr(main_module, "LeonardoClient", StubLeoClient)
    monkeypatch.setattr(main_module, "CanvaClient", StubCanvaClient)
    monkeypatch.setattr(main_module, "download_to_file", fake_download)
    monkeypatch.setattr(main_module, "DEFAULT_OUTPUT_ROOT", tmp_path)

    parser = main_module.create_parser()
    args = parser.parse_args(["generate-api", "social_banner_bg", "--sync", "--run-id", "run_fixed"])

    assert main_module.run_generate_api(args, _config()) == 0
    assert main_module.run_generate_api(args, _config()) == 0

    assert call_counts["generation"] == 1
    assert call_counts["download"] == 1
    assert call_counts["upload"] == 1

    entries = _read_ledger(tmp_path / "ledger.jsonl")
    assert sum(1 for entry in entries if entry["stage"] == "generation" and entry["status"] == "success") == 1
    assert sum(1 for entry in entries if entry["stage"] == "download_raw" and entry["status"] == "success") == 1
    assert sum(1 for entry in entries if entry["stage"] == "sync" and entry["status"] == "success") == 1


def test_generate_api_retries_export_when_ledger_path_missing(monkeypatch, tmp_path):
    call_counts = {
        "autofill": 0,
        "export": 0,
    }

    class StubLeoClient:
        def generate_and_wait(self, **kwargs):
            return {
                "generation_id": "gen_1",
                "urls": ["https://example.com/image.png"],
                "status_payload": {"ok": True},
            }

    class StubCanvaClient:
        def autofill_template(self, template_id, data):
            call_counts["autofill"] += 1
            return "autofill_1"

        def wait_for_autofill_job(self, job_id):
            return {"job_id": job_id, "design_id": "design_1"}

        def export_design(self, design_id, format_type="png"):
            call_counts["export"] += 1
            return "export_1"

        def wait_for_export_job(self, job_id):
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
            "--run-id",
            "run_export_retry",
        ]
    )

    assert main_module.run_generate_api(args, _config()) == 0

    export_file = tmp_path / "exports" / "run_export_retry" / "social_banner_bg_run_export_retry.png"
    assert export_file.exists()
    export_file.unlink()

    assert main_module.run_generate_api(args, _config()) == 0
    assert call_counts["autofill"] == 1
    assert call_counts["export"] == 2


def test_generate_api_logs_failed_generation_stage(monkeypatch, tmp_path):
    class StubLeoClient:
        def generate_and_wait(self, **kwargs):
            raise RuntimeError("generation crash")

    monkeypatch.setattr(main_module, "LeonardoClient", StubLeoClient)
    monkeypatch.setattr(main_module, "DEFAULT_OUTPUT_ROOT", tmp_path)

    parser = main_module.create_parser()
    args = parser.parse_args(["generate-api", "social_banner_bg"])

    with pytest.raises(RuntimeError, match="generation crash"):
        main_module.run_generate_api(args, _config())

    entries = _read_ledger(tmp_path / "ledger.jsonl")
    _assert_stage_failed(entries, "generation")


def test_generate_api_logs_failed_download_stage(monkeypatch, tmp_path):
    class StubLeoClient:
        def generate_and_wait(self, **kwargs):
            return {
                "generation_id": "gen_1",
                "urls": ["https://example.com/image.png"],
            }

    def fake_download(url, output_path, timeout_seconds=60):
        raise RuntimeError("download crash")

    monkeypatch.setattr(main_module, "LeonardoClient", StubLeoClient)
    monkeypatch.setattr(main_module, "download_to_file", fake_download)
    monkeypatch.setattr(main_module, "DEFAULT_OUTPUT_ROOT", tmp_path)

    parser = main_module.create_parser()
    args = parser.parse_args(["generate-api", "social_banner_bg"])

    with pytest.raises(RuntimeError, match="download crash"):
        main_module.run_generate_api(args, _config())

    entries = _read_ledger(tmp_path / "ledger.jsonl")
    _assert_stage_failed(entries, "download_raw")


def test_generate_api_logs_failed_sync_stage(monkeypatch, tmp_path):
    class StubLeoClient:
        def generate_and_wait(self, **kwargs):
            return {
                "generation_id": "gen_1",
                "urls": ["https://example.com/image.png"],
            }

    class StubCanvaClient:
        def get_or_create_shadowpunk_folder(self, folder_path):
            raise RuntimeError("sync crash")

    def fake_download(url, output_path, timeout_seconds=60):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"fake")

    monkeypatch.setattr(main_module, "LeonardoClient", StubLeoClient)
    monkeypatch.setattr(main_module, "CanvaClient", StubCanvaClient)
    monkeypatch.setattr(main_module, "download_to_file", fake_download)
    monkeypatch.setattr(main_module, "DEFAULT_OUTPUT_ROOT", tmp_path)

    parser = main_module.create_parser()
    args = parser.parse_args(["generate-api", "social_banner_bg", "--sync"])

    with pytest.raises(RuntimeError, match="sync crash"):
        main_module.run_generate_api(args, _config())

    entries = _read_ledger(tmp_path / "ledger.jsonl")
    _assert_stage_failed(entries, "sync")


def test_generate_api_logs_failed_autofill_stage(monkeypatch, tmp_path):
    class StubLeoClient:
        def generate_and_wait(self, **kwargs):
            return {
                "generation_id": "gen_1",
                "urls": ["https://example.com/image.png"],
            }

    class StubCanvaClient:
        def autofill_template(self, template_id, data):
            raise RuntimeError("autofill crash")

    def fake_download(url, output_path, timeout_seconds=60):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"fake")

    monkeypatch.setattr(main_module, "LeonardoClient", StubLeoClient)
    monkeypatch.setattr(main_module, "CanvaClient", StubCanvaClient)
    monkeypatch.setattr(main_module, "download_to_file", fake_download)
    monkeypatch.setattr(main_module, "DEFAULT_OUTPUT_ROOT", tmp_path)

    parser = main_module.create_parser()
    args = parser.parse_args(["generate-api", "social_banner_bg", "--autofill"])

    with pytest.raises(RuntimeError, match="autofill crash"):
        main_module.run_generate_api(args, _config())

    entries = _read_ledger(tmp_path / "ledger.jsonl")
    _assert_stage_failed(entries, "autofill")


def test_generate_api_logs_failed_export_stage(monkeypatch, tmp_path):
    class StubLeoClient:
        def generate_and_wait(self, **kwargs):
            return {
                "generation_id": "gen_1",
                "urls": ["https://example.com/image.png"],
            }

    class StubCanvaClient:
        def autofill_template(self, template_id, data):
            return "autofill_1"

        def wait_for_autofill_job(self, job_id):
            return {"job_id": job_id, "design_id": "design_1"}

        def export_design(self, design_id, format_type="png"):
            raise RuntimeError("export crash")

    def fake_download(url, output_path, timeout_seconds=60):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"fake")

    monkeypatch.setattr(main_module, "LeonardoClient", StubLeoClient)
    monkeypatch.setattr(main_module, "CanvaClient", StubCanvaClient)
    monkeypatch.setattr(main_module, "download_to_file", fake_download)
    monkeypatch.setattr(main_module, "DEFAULT_OUTPUT_ROOT", tmp_path)

    parser = main_module.create_parser()
    args = parser.parse_args(["generate-api", "social_banner_bg", "--autofill", "--export", "png"])

    with pytest.raises(RuntimeError, match="export crash"):
        main_module.run_generate_api(args, _config())

    entries = _read_ledger(tmp_path / "ledger.jsonl")
    _assert_stage_failed(entries, "export")
