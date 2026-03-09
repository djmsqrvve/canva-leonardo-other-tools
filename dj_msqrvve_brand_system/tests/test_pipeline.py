from pathlib import Path

from lib.pipeline import (
    append_ledger_event,
    build_ledger_event,
    ensure_output_dirs,
    find_stage_success,
    make_idempotency_key,
)


def test_ensure_output_dirs(tmp_path):
    result = ensure_output_dirs(str(tmp_path), "run123")
    assert result["raw"].exists()
    assert result["canva"].exists()
    assert result["exports"].exists()
    assert result["ledger"] == Path(tmp_path) / "ledger.jsonl"


def test_make_idempotency_key_is_stable():
    first = make_idempotency_key("run1", "asset1", "prompt")
    second = make_idempotency_key("run1", "asset1", "prompt")
    third = make_idempotency_key("run2", "asset1", "prompt")
    assert first == second
    assert first != third


def test_append_and_find_stage_success(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    event = build_ledger_event(
        run_id="run123",
        asset_key="social_banner_bg",
        idempotency_key="run123:social_banner_bg:hash",
        stage="sync",
        status="success",
        canva_asset_id="asset_123",
    )
    append_ledger_event(ledger_path, event)

    found = find_stage_success(ledger_path, "run123:social_banner_bg:hash", "sync")
    assert found is not None
    assert found["canva_asset_id"] == "asset_123"
