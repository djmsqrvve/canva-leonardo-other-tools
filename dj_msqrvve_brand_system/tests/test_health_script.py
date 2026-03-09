from datetime import UTC, datetime
from pathlib import Path

import test_health as health_module


def test_make_smoke_run_id_is_stable_for_given_timestamp():
    run_id = health_module.make_smoke_run_id(
        "social_banner_bg",
        "autofill export",
        now=datetime(2026, 3, 9, 12, 34, 56, tzinfo=UTC),
    )

    assert run_id == "smoke-social-banner-bg-autofill-export-20260309123456"


def test_collect_local_state_reports_missing_template_override(monkeypatch, tmp_path):
    prompts_dir = tmp_path / "config"
    prompts_dir.mkdir()
    (prompts_dir / "prompts.yaml").write_text(
        (
            "models: {phoenix: model_123}\n"
            "prompts:\n"
            "  social_banner_bg:\n"
            "    model: phoenix\n"
            "    prompt: hello world\n"
            "canva_templates:\n"
            "  social_banner_bg: TEMPLATE_ID_HERE\n"
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(health_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(health_module, "DEFAULT_OUTPUT_ROOT", tmp_path / "outputs")
    monkeypatch.setattr(
        health_module,
        "load_prompts",
        lambda: {
            "models": {"phoenix": "model_123"},
            "prompts": {"social_banner_bg": {"model": "phoenix", "prompt": "hello world"}},
            "canva_templates": {"social_banner_bg": "TEMPLATE_ID_HERE"},
        },
    )

    state = health_module.collect_local_state("social_banner_bg")

    assert state["prompt_ready"] is True
    assert state["template_ready"] is False
    assert "prompts.local.yaml" in state["template_summary"]
    assert state["browser_profile_seeded"] is False
    assert state["paths"]["ledger"] == tmp_path / "outputs" / "ledger.jsonl"


def test_build_smoke_plan_blocks_export_until_template_ready():
    state = {
        "asset_key": "social_banner_bg",
        "prompt_ready": True,
        "template_ready": False,
        "template_summary": "Add a private template ID first.",
        "browser_profile_seeded": False,
        "has_leonardo_key": True,
        "has_canva_access_token": True,
        "has_canva_refresh_token": False,
        "has_canva_client_credentials": False,
        "paths": {
            "ledger": Path("/tmp/ledger.jsonl"),
            "browser_artifacts": Path("/tmp/browser-artifacts"),
            "dashboard_jobs": Path("/tmp/dashboard-jobs.json"),
            "prompts_local": Path("/tmp/prompts.local.yaml"),
            "profile": Path("/tmp/user_profile"),
        },
        "env_file_exists": True,
        "prompts_local_exists": False,
    }

    plan = health_module.build_smoke_plan(
        asset_key="social_banner_bg",
        export_format="png",
        canva_folder="Shadowpunk/Generations",
        browser_prompt="simple smoke",
        state=state,
        now=datetime(2026, 3, 9, 12, 34, 56, tzinfo=UTC),
    )

    export_step = next(step for step in plan if step["name"] == "Canva autofill and export")
    browser_step = next(step for step in plan if step["name"] == "Browser headless smoke")

    assert export_step["status"] == "blocked"
    assert export_step["summary"] == "Add a private template ID first."
    assert "smoke-social-banner-bg-export-20260309123456" in export_step["command"]
    assert browser_step["status"] == "blocked"


def test_run_auth_command_returns_failure_when_any_provider_fails(monkeypatch):
    monkeypatch.setattr(
        health_module,
        "check_leonardo_auth",
        lambda: health_module.build_live_check_result("Leonardo auth", "ok", "ok"),
    )
    monkeypatch.setattr(
        health_module,
        "check_canva_auth",
        lambda: health_module.build_live_check_result("Canva auth", "failed", "boom"),
    )

    assert health_module.run_auth_command("all") == 1
