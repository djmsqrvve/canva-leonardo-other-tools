from __future__ import annotations

import argparse
import os
import re
from datetime import UTC, datetime
from typing import Any

from apis.canva_api import CanvaClient
from apis.leonardo_api import LeonardoClient
from lib.errors import ConfigurationError
from main import (
    DEFAULT_CANVA_FOLDER,
    DEFAULT_OUTPUT_ROOT,
    PROJECT_ROOT,
    PROMPTS_LOCAL_EXAMPLE_PATH,
    PROMPTS_LOCAL_OVERRIDE_PATH,
    load_environment as load_project_environment,
    load_prompts,
    resolve_canva_template_id,
)

DEFAULT_ASSET_KEY = "social_banner_bg"
DEFAULT_BROWSER_PROMPT = "simple lighting smoke prompt"
STATUS_ICONS = {
    "ok": "OK",
    "ready": "READY",
    "manual": "MANUAL",
    "blocked": "BLOCKED",
    "failed": "FAILED",
}


def load_environment() -> None:
    load_project_environment()


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "smoke"


def make_smoke_run_id(asset_key: str, label: str, *, now: datetime | None = None) -> str:
    timestamp = (now or datetime.now(UTC)).strftime("%Y%m%d%H%M%S")
    return f"smoke-{_slug(asset_key)}-{_slug(label)}-{timestamp}"


def format_check_line(result: dict[str, Any]) -> str:
    icon = STATUS_ICONS.get(result["status"], result["status"].upper())
    return f"[{icon}] {result['name']}: {result['summary']}"


def build_live_check_result(
    name: str,
    status: str,
    summary: str,
    *,
    details: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "summary": summary,
        "details": details or [],
    }


def check_leonardo_auth() -> dict[str, Any]:
    api_key = os.environ.get("LEONARDO_API_KEY", "").strip()
    if not api_key:
        return build_live_check_result(
            "Leonardo auth",
            "blocked",
            "LEONARDO_API_KEY is not set in .env.",
        )

    try:
        client = LeonardoClient(api_key=api_key)
        payload = client._request("GET", "/me")
        user_details = payload.get("user_details") or payload.get("user") or {}
        user_id = user_details.get("id") or user_details.get("user_id")
        details = [f"user_id={user_id}"] if user_id else []
        return build_live_check_result(
            "Leonardo auth",
            "ok",
            "Leonardo API authentication succeeded.",
            details=details,
        )
    except Exception as exc:  # noqa: BLE001
        return build_live_check_result(
            "Leonardo auth",
            "failed",
            f"{type(exc).__name__}: {exc}",
        )


def check_canva_auth() -> dict[str, Any]:
    access_token = os.environ.get("CANVA_ACCESS_TOKEN", "").strip()
    refresh_token = os.environ.get("CANVA_REFRESH_TOKEN", "").strip()
    client_id = os.environ.get("CANVA_CLIENT_ID", "").strip()
    client_secret = os.environ.get("CANVA_CLIENT_SECRET", "").strip()

    if not access_token and not refresh_token:
        return build_live_check_result(
            "Canva auth",
            "blocked",
            "CANVA_ACCESS_TOKEN or CANVA_REFRESH_TOKEN must be set in .env.",
        )

    try:
        client = CanvaClient()
        payload = client.get_current_user()
        user = payload.get("user", {})
        display_name = user.get("display_name") or user.get("name") or "Unknown"
        details = [f"display_name={display_name}"]
        if refresh_token and client_id and client_secret:
            details.append("refresh_flow=ready")
        elif refresh_token:
            details.append("refresh_flow=blocked (missing client credentials)")
        return build_live_check_result(
            "Canva auth",
            "ok",
            "Canva authentication succeeded.",
            details=details,
        )
    except Exception as exc:  # noqa: BLE001
        return build_live_check_result(
            "Canva auth",
            "failed",
            f"{type(exc).__name__}: {exc}",
        )


def load_effective_config_status(asset_key: str) -> dict[str, Any]:
    try:
        config = load_prompts()
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "failed",
            "summary": f"Failed to load prompt config: {type(exc).__name__}: {exc}",
            "asset_exists": False,
            "template_ready": False,
            "template_summary": "Prompt config did not load.",
        }

    prompt_exists = asset_key in config.get("prompts", {})
    template_status = "blocked"
    template_summary = f"No prompt configuration found for '{asset_key}'."

    if prompt_exists:
        template_summary = (
            f"No Canva template ID configured for '{asset_key}'. "
            f"Copy {PROMPTS_LOCAL_EXAMPLE_PATH} to {PROMPTS_LOCAL_OVERRIDE_PATH} and add a real template ID."
        )
        try:
            template_id = resolve_canva_template_id(config, asset_key)
            template_status = "ready"
            template_summary = f"Resolved Canva template ID for '{asset_key}' ({template_id})."
        except ConfigurationError as exc:
            template_summary = str(exc)

    return {
        "status": "ready" if prompt_exists else "blocked",
        "summary": (
            f"Prompt config is ready for '{asset_key}'."
            if prompt_exists
            else f"No prompt configuration found for '{asset_key}'."
        ),
        "asset_exists": prompt_exists,
        "template_ready": template_status == "ready",
        "template_summary": template_summary,
    }


def collect_local_state(asset_key: str) -> dict[str, Any]:
    output_root = DEFAULT_OUTPUT_ROOT
    profile_path = PROJECT_ROOT / "user_profile"
    prompts_local_path = PROJECT_ROOT / PROMPTS_LOCAL_OVERRIDE_PATH
    config_status = load_effective_config_status(asset_key)

    return {
        "asset_key": asset_key,
        "env_file_exists": (PROJECT_ROOT / ".env").exists(),
        "prompts_local_exists": prompts_local_path.exists(),
        "prompt_ready": config_status["asset_exists"],
        "template_ready": config_status["template_ready"],
        "template_summary": config_status["template_summary"],
        "browser_profile_seeded": profile_path.exists() and any(profile_path.iterdir()),
        "has_leonardo_key": bool(os.environ.get("LEONARDO_API_KEY", "").strip()),
        "has_canva_access_token": bool(os.environ.get("CANVA_ACCESS_TOKEN", "").strip()),
        "has_canva_refresh_token": bool(os.environ.get("CANVA_REFRESH_TOKEN", "").strip()),
        "has_canva_client_credentials": all(
            os.environ.get(name, "").strip()
            for name in ("CANVA_CLIENT_ID", "CANVA_CLIENT_SECRET")
        ),
        "paths": {
            "ledger": output_root / "ledger.jsonl",
            "browser_artifacts": output_root / "browser-artifacts",
            "dashboard_jobs": output_root / "dashboard-jobs.json",
            "prompts_local": prompts_local_path,
            "profile": profile_path,
        },
    }


def build_smoke_plan(
    *,
    asset_key: str,
    export_format: str,
    canva_folder: str,
    browser_prompt: str,
    state: dict[str, Any],
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    api_run_id = make_smoke_run_id(asset_key, "api", now=now)
    sync_run_id = make_smoke_run_id(asset_key, "sync", now=now)
    export_run_id = make_smoke_run_id(asset_key, "export", now=now)

    leonardo_ready = state["prompt_ready"] and state["has_leonardo_key"]
    canva_ready = state["has_canva_access_token"] or state["has_canva_refresh_token"]
    export_ready = state["template_ready"] and canva_ready

    plan.append(
        {
            "name": "Live auth checks",
            "status": "ready" if state["has_leonardo_key"] or canva_ready else "blocked",
            "command": "python src/test_health.py auth",
            "summary": "Verify Leonardo and Canva credentials against the live providers.",
        }
    )
    plan.append(
        {
            "name": "Leonardo API generation",
            "status": "ready" if leonardo_ready else "blocked",
            "command": f"python src/main.py generate-api {asset_key} --run-id {api_run_id}",
            "summary": "Exercise the live Leonardo API and write a ledger-backed run.",
        }
    )
    plan.append(
        {
            "name": "Canva sync",
            "status": "ready" if leonardo_ready and canva_ready else "blocked",
            "command": (
                f"python src/main.py generate-api {asset_key} --sync "
                f'--canva-folder "{canva_folder}" --run-id {sync_run_id}'
            ),
            "summary": "Generate via Leonardo and upload the raw result into Canva.",
        }
    )
    plan.append(
        {
            "name": "Canva autofill and export",
            "status": "ready" if leonardo_ready and export_ready else "blocked",
            "command": (
                f"python src/main.py generate-api {asset_key} --autofill --export {export_format} "
                f"--run-id {export_run_id}"
            ),
            "summary": state["template_summary"]
            if not export_ready
            else "Run live Canva autofill and export for the configured template mapping.",
        }
    )
    plan.append(
        {
            "name": "Browser bootstrap or refresh",
            "status": "manual",
            "command": f'python src/main.py generate-browser "{browser_prompt}"',
            "summary": "Run interactively if the saved Leonardo browser session is missing or expired.",
        }
    )
    plan.append(
        {
            "name": "Browser headless smoke",
            "status": "ready" if state["browser_profile_seeded"] else "blocked",
            "command": f'python src/main.py generate-browser "{browser_prompt}" --headless',
            "summary": (
                "Verify the bootstrapped browser profile can still generate headlessly."
                if state["browser_profile_seeded"]
                else "Seed user_profile/ with an interactive browser run first."
            ),
        }
    )
    plan.append(
        {
            "name": "Dashboard restart recovery",
            "status": "manual",
            "command": "npm run dev",
            "summary": (
                "Queue a job, stop the dashboard once it reaches running, restart it, "
                "then confirm the interrupted job is marked failed and retryable."
            ),
        }
    )
    return plan


def render_local_state(state: dict[str, Any]) -> None:
    print("Local state")
    print(f"- .env present: {'yes' if state['env_file_exists'] else 'no'}")
    print(f"- Prompt configured for {state['asset_key']}: {'yes' if state['prompt_ready'] else 'no'}")
    print(f"- prompts.local.yaml present: {'yes' if state['prompts_local_exists'] else 'no'}")
    print(f"- Template override ready: {'yes' if state['template_ready'] else 'no'}")
    print(f"  {state['template_summary']}")
    print(f"- Browser profile seeded: {'yes' if state['browser_profile_seeded'] else 'no'}")
    print(f"- Ledger path: {state['paths']['ledger']}")
    print(f"- Browser artifacts: {state['paths']['browser_artifacts']}")
    print(f"- Dashboard jobs: {state['paths']['dashboard_jobs']}")


def render_live_checks(results: list[dict[str, Any]]) -> None:
    print("Live auth checks")
    for result in results:
        print(f"- {format_check_line(result)}")
        for detail in result["details"]:
            print(f"  {detail}")


def render_smoke_plan(plan: list[dict[str, Any]]) -> None:
    print("Manual live smoke plan")
    for step in plan:
        print(f"- {format_check_line(step)}")
        print(f"  {step['command']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manual live-provider health and smoke helper")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("auth", "state", "smoke-plan"),
        default="auth",
        help="auth (default), state, or smoke-plan",
    )
    parser.add_argument(
        "--check",
        choices=("all", "leonardo", "canva"),
        default="all",
        help="Restrict auth checks to a single provider",
    )
    parser.add_argument(
        "--asset-key",
        default=DEFAULT_ASSET_KEY,
        help=f"Prompt asset key to use when planning live smoke runs (default: {DEFAULT_ASSET_KEY})",
    )
    parser.add_argument(
        "--export-format",
        default="png",
        help="Export format to include in the live smoke plan (default: png)",
    )
    parser.add_argument(
        "--canva-folder",
        default=DEFAULT_CANVA_FOLDER,
        help=f"Canva folder path for the sync smoke step (default: {DEFAULT_CANVA_FOLDER})",
    )
    parser.add_argument(
        "--browser-prompt",
        default=DEFAULT_BROWSER_PROMPT,
        help="Prompt to use for browser smoke guidance",
    )
    return parser.parse_args()


def run_auth_command(check: str) -> int:
    requested_checks: list[dict[str, Any]] = []
    if check in {"all", "leonardo"}:
        requested_checks.append(check_leonardo_auth())
    if check in {"all", "canva"}:
        requested_checks.append(check_canva_auth())

    render_live_checks(requested_checks)
    return 0 if all(result["status"] == "ok" for result in requested_checks) else 1


def run_state_command(asset_key: str) -> int:
    state = collect_local_state(asset_key)
    render_local_state(state)
    return 0 if state["prompt_ready"] else 1


def run_smoke_plan_command(
    *,
    asset_key: str,
    export_format: str,
    canva_folder: str,
    browser_prompt: str,
) -> int:
    state = collect_local_state(asset_key)
    render_local_state(state)
    print()
    plan = build_smoke_plan(
        asset_key=asset_key,
        export_format=export_format,
        canva_folder=canva_folder,
        browser_prompt=browser_prompt,
        state=state,
    )
    render_smoke_plan(plan)
    return 0 if all(step["status"] != "blocked" for step in plan) else 1


def main() -> int:
    load_environment()
    args = parse_args()

    if args.command == "auth":
        return run_auth_command(args.check)
    if args.command == "state":
        return run_state_command(args.asset_key)
    if args.command == "smoke-plan":
        return run_smoke_plan_command(
            asset_key=args.asset_key,
            export_format=args.export_format,
            canva_folder=args.canva_folder,
            browser_prompt=args.browser_prompt,
        )
    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
