"""Shared utility helpers for retries, polling, and downloads."""

from __future__ import annotations

import time
from typing import Any, Callable, Iterable, Optional, Sequence

import requests

from lib.errors import ApiResponseError, TimeoutError, handle_request_exception


def compute_backoff_schedule(
    *,
    attempts: int,
    initial_delay_seconds: float = 1.0,
    backoff_factor: float = 1.5,
    max_delay_seconds: float = 10.0,
) -> list[float]:
    """Return deterministic backoff delays per poll attempt."""
    delays: list[float] = []
    delay = max(initial_delay_seconds, 0.0)
    for _ in range(max(attempts, 0)):
        delays.append(min(delay, max_delay_seconds))
        delay *= max(backoff_factor, 1.0)
    return delays


def extract_nested(payload: dict[str, Any], paths: Sequence[str]) -> Optional[Any]:
    """Return first non-null value from dot-delimited payload paths."""
    for path in paths:
        current: Any = payload
        found = True
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                found = False
                break
            current = current[part]
        if found and current is not None:
            return current
    return None


def poll_job(
    job_id: str,
    api_type: str,
    status_fetcher: Callable[[str], dict[str, Any]],
    *,
    status_extractor: Callable[[dict[str, Any]], Optional[str]],
    success_statuses: Iterable[str],
    failure_statuses: Iterable[str],
    max_attempts: int = 15,
    initial_delay_seconds: float = 1.0,
    backoff_factor: float = 1.5,
    max_delay_seconds: float = 10.0,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Poll an async job until completion or timeout."""
    if max_attempts <= 0:
        raise ValueError("max_attempts must be greater than zero.")

    success = {value.lower() for value in success_statuses}
    failure = {value.lower() for value in failure_statuses}
    delays = compute_backoff_schedule(
        attempts=max_attempts,
        initial_delay_seconds=initial_delay_seconds,
        backoff_factor=backoff_factor,
        max_delay_seconds=max_delay_seconds,
    )

    last_status = "unknown"
    for attempt, delay in enumerate(delays, start=1):
        payload = status_fetcher(job_id)
        status = (status_extractor(payload) or "").strip().lower()
        last_status = status or "unknown"

        if status in success:
            return payload
        if status in failure:
            raise ApiResponseError(
                f"{api_type} job {job_id} failed with status '{status or 'unknown'}'"
            )
        if attempt < max_attempts:
            sleep_fn(delay)

    raise TimeoutError(
        f"{api_type} job {job_id} did not finish after {max_attempts} attempts "
        f"(last status: {last_status})"
    )


def download_to_file(url: str, output_path: str, *, timeout_seconds: int = 60) -> None:
    """Download a URL to a local file path."""
    try:
        response = requests.get(url, timeout=timeout_seconds)
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        handle_request_exception(exc, f"download from {url}")

    with open(output_path, "wb") as file_obj:
        file_obj.write(response.content)
