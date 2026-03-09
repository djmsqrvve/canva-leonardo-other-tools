"""Pipeline helpers for run IDs, deterministic paths, and ledger tracing."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


DEFAULT_LEDGER_FILE = "ledger.jsonl"


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def generate_run_id() -> str:
    return uuid4().hex[:12]


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def make_idempotency_key(run_id: str, asset_key: str, prompt: str) -> str:
    return f"{run_id}:{asset_key}:{prompt_hash(prompt)}"


def ensure_output_dirs(base_output_dir: str, run_id: str) -> dict[str, Path]:
    root = Path(base_output_dir)
    raw_dir = root / "raw" / run_id
    canva_dir = root / "canva" / run_id
    export_dir = root / "exports" / run_id

    for directory in (raw_dir, canva_dir, export_dir):
        directory.mkdir(parents=True, exist_ok=True)

    return {
        "root": root,
        "raw": raw_dir,
        "canva": canva_dir,
        "exports": export_dir,
        "ledger": root / DEFAULT_LEDGER_FILE,
    }


def build_ledger_event(
    *,
    run_id: str,
    asset_key: str,
    idempotency_key: str,
    stage: str,
    status: str,
    generation_id: Optional[str] = None,
    image_url: Optional[str] = None,
    local_path: Optional[str] = None,
    canva_asset_id: Optional[str] = None,
    design_id: Optional[str] = None,
    export_path: Optional[str] = None,
    error: Optional[str] = None,
    extras: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "timestamp": utc_now_iso(),
        "run_id": run_id,
        "asset_key": asset_key,
        "idempotency_key": idempotency_key,
        "stage": stage,
        "status": status,
        "generation_id": generation_id,
        "image_url": image_url,
        "local_path": local_path,
        "canva_asset_id": canva_asset_id,
        "design_id": design_id,
        "export_path": export_path,
        "error": error,
    }
    if extras:
        payload.update(extras)
    return payload


def append_ledger_event(ledger_path: str | Path, event: dict[str, Any]) -> None:
    ledger = Path(ledger_path)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as file_obj:
        file_obj.write(json.dumps(event, sort_keys=True) + "\n")


def find_stage_success(
    ledger_path: str | Path, idempotency_key: str, stage: str
) -> Optional[dict[str, Any]]:
    ledger = Path(ledger_path)
    if not ledger.exists():
        return None

    latest_match: Optional[dict[str, Any]] = None
    with ledger.open("r", encoding="utf-8") as file_obj:
        for line in file_obj:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue

            if (
                payload.get("idempotency_key") == idempotency_key
                and payload.get("stage") == stage
                and payload.get("status") == "success"
            ):
                latest_match = payload
    return latest_match
