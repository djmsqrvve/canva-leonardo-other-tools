"""Failure artifact capture for browser automation."""
from __future__ import annotations

import json
import time
from pathlib import Path


def capture_failure_artifacts(
    driver,
    artifact_root: Path,
    phase: str,
    reason: str,
    *,
    headless: bool = False,
) -> dict[str, str]:
    """Save screenshot, page source, and metadata for a browser failure.

    Returns a dict mapping artifact type to file path.
    """
    artifact_dir = artifact_root / f"{int(time.time() * 1000)}-{phase}"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, str] = {}

    screenshot_path = artifact_dir / "screenshot.png"
    try:
        if driver.save_screenshot(str(screenshot_path)):
            artifacts["screenshot"] = str(screenshot_path)
    except Exception:  # noqa: BLE001
        pass

    page_source = getattr(driver, "page_source", None)
    if isinstance(page_source, str):
        page_source_path = artifact_dir / "page.html"
        page_source_path.write_text(page_source, encoding="utf-8")
        artifacts["page_source"] = str(page_source_path)

    metadata = {
        "phase": phase,
        "reason": reason,
        "headless": headless,
        "current_url": getattr(driver, "current_url", ""),
    }
    metadata_path = artifact_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    artifacts["metadata"] = str(metadata_path)
    return artifacts


def format_artifact_hint(artifacts: dict[str, str]) -> str:
    if not artifacts:
        return ""
    parts = [f"{key}={value}" for key, value in sorted(artifacts.items())]
    return f"Artifacts: {', '.join(parts)}."
