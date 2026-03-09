import argparse
import os
from importlib import import_module
from pathlib import Path
from urllib.parse import urlparse

import yaml
from dotenv import load_dotenv

from apis.canva_api import CanvaClient
from apis.leonardo_api import LeonardoClient
from lib.errors import ApiResponseError, ConfigurationError, OptionalDependencyError
from lib.pipeline import (
    append_ledger_event,
    build_ledger_event,
    ensure_output_dirs,
    find_stage_success,
    generate_run_id,
    make_idempotency_key,
)
from lib.utils import download_to_file


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs"
DEFAULT_CANVA_FOLDER = "Shadowpunk/Generations"
EXPORT_FORMATS = ("png", "jpg", "pdf", "mp4")
PROMPTS_CONFIG_PATH = Path("config/prompts.yaml")
PROMPTS_LOCAL_OVERRIDE_PATH = Path("config/prompts.local.yaml")
PROMPTS_LOCAL_EXAMPLE_PATH = Path("config/prompts.local.example.yaml")
PLACEHOLDER_CANVA_TEMPLATE_ID = "TEMPLATE_ID_HERE"


def load_environment() -> None:
    env_path = PROJECT_ROOT / ".env"
    load_dotenv(env_path)


def load_yaml_mapping(path: Path, *, label: str) -> dict:
    with path.open("r", encoding="utf-8") as file_obj:
        payload = yaml.safe_load(file_obj)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ConfigurationError(f"{label} must contain a top-level mapping.")
    return payload


def normalize_canva_templates(raw_templates: object, *, source: str) -> dict[str, str]:
    if raw_templates is None:
        return {}
    if not isinstance(raw_templates, dict):
        raise ConfigurationError(f"{source} must define canva_templates as a mapping.")

    normalized: dict[str, str] = {}
    for asset_key, template_id in raw_templates.items():
        if not isinstance(asset_key, str) or not asset_key.strip():
            raise ConfigurationError(f"{source} contains an empty canva_templates key.")
        if not isinstance(template_id, str):
            raise ConfigurationError(
                f"{source} contains a non-string canva_templates value for '{asset_key}'."
            )

        cleaned_template_id = template_id.strip()
        if not cleaned_template_id:
            raise ConfigurationError(
                f"{source} contains an empty Canva template ID for '{asset_key}'."
            )
        normalized[asset_key.strip()] = cleaned_template_id
    return normalized


def load_prompts() -> dict:
    config_path = PROJECT_ROOT / PROMPTS_CONFIG_PATH
    config = load_yaml_mapping(config_path, label=str(PROMPTS_CONFIG_PATH))
    config["canva_templates"] = normalize_canva_templates(
        config.get("canva_templates"),
        source=str(PROMPTS_CONFIG_PATH),
    )

    override_path = PROJECT_ROOT / PROMPTS_LOCAL_OVERRIDE_PATH
    if not override_path.exists():
        return config

    overrides = load_yaml_mapping(override_path, label=str(PROMPTS_LOCAL_OVERRIDE_PATH))
    unexpected_keys = set(overrides) - {"canva_templates"}
    if unexpected_keys:
        unexpected = ", ".join(sorted(unexpected_keys))
        raise ConfigurationError(
            f"{PROMPTS_LOCAL_OVERRIDE_PATH} only supports canva_templates overrides; found: {unexpected}."
        )

    override_templates = normalize_canva_templates(
        overrides.get("canva_templates"),
        source=str(PROMPTS_LOCAL_OVERRIDE_PATH),
    )
    if override_templates:
        config["canva_templates"] = {
            **config.get("canva_templates", {}),
            **override_templates,
        }
    return config


def resolve_canva_template_id(config: dict, asset_key: str) -> str:
    template_id = normalize_canva_templates(
        config.get("canva_templates"),
        source="effective config",
    ).get(asset_key)
    if not template_id:
        raise ConfigurationError(
            f"No Canva template ID configured for '{asset_key}'. "
            f"Add it to {PROMPTS_LOCAL_OVERRIDE_PATH} "
            f"(copy {PROMPTS_LOCAL_EXAMPLE_PATH}) before using --autofill or --export."
        )
    if template_id == PLACEHOLDER_CANVA_TEMPLATE_ID:
        raise ConfigurationError(
            f"Placeholder Canva template ID configured for '{asset_key}'. "
            f"Set a real private ID in {PROMPTS_LOCAL_OVERRIDE_PATH} "
            f"(copy {PROMPTS_LOCAL_EXAMPLE_PATH}) before using --autofill or --export."
        )
    return template_id


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DJ MSQRVVE Brand System CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    browser_parser = subparsers.add_parser(
        "generate-browser",
        help="Generate assets via automated browser (Free tokens)",
    )
    browser_parser.add_argument("prompt_key", help="Key from prompts.yaml or a custom prompt string")
    browser_parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")

    api_parser = subparsers.add_parser(
        "generate-api",
        help="Generate assets via Production API (Requires Credits)",
    )
    api_parser.add_argument("asset_type", help="Asset type key from prompts.yaml")
    api_parser.add_argument("--sync", action="store_true", help="Upload generated asset to Canva")
    api_parser.add_argument(
        "--autofill",
        action="store_true",
        help="Run Canva template autofill after generation",
    )
    api_parser.add_argument(
        "--export",
        dest="export_format",
        nargs="?",
        choices=EXPORT_FORMATS,
        const="png",
        help="Export Canva design output (defaults to png when flag is present)",
    )
    api_parser.add_argument(
        "--canva-folder",
        default=DEFAULT_CANVA_FOLDER,
        help=f"Target Canva folder path for sync (default: {DEFAULT_CANVA_FOLDER})",
    )
    api_parser.add_argument(
        "--run-id",
        default=None,
        help="Optional run ID for idempotent retries",
    )
    return parser


def url_extension(url: str, fallback: str = ".png") -> str:
    path = urlparse(url).path
    extension = Path(path).suffix.lower()
    return extension if extension else fallback


def create_leonardo_browser(*, headless: bool):
    try:
        browser_module = import_module("lib.leonardo_browser")
    except ModuleNotFoundError as exc:
        if exc.name in {"selenium", "webdriver_manager"}:
            raise OptionalDependencyError(
                "Browser generation requires optional dependencies. "
                "Install dj_msqrvve_brand_system/requirements-browser.txt "
                "and then rerun the command."
            ) from exc
        raise
    return browser_module.LeonardoBrowser(headless=headless)


def run_generate_browser(args: argparse.Namespace, config: dict) -> int:
    prompt = config.get("prompts", {}).get(args.prompt_key, {}).get("prompt", args.prompt_key)
    print("--- Starting Browser Automation Pipeline ---")
    browser = create_leonardo_browser(headless=args.headless)
    try:
        browser.login()
        image_urls = browser.generate(prompt)
        if image_urls:
            print(f"✅ Success! Retrieved {len(image_urls)} images:")
            for index, url in enumerate(image_urls):
                print(f"   [{index}] {url}")
            return 0
        print("❌ Generation failed or no images found.")
        return 1
    finally:
        print("Closing browser...")
        browser.close()


def run_generate_api(args: argparse.Namespace, config: dict) -> int:
    asset_key = args.asset_type
    prompt_data = config.get("prompts", {}).get(asset_key)
    if not prompt_data:
        raise ValueError(f"No prompt configuration found for '{asset_key}' in prompts.yaml")

    if args.export_format and not args.autofill:
        raise ValueError("--export requires --autofill to produce a design to export")

    run_id = args.run_id or generate_run_id()
    output_dirs = ensure_output_dirs(str(DEFAULT_OUTPUT_ROOT), run_id)
    ledger_path = output_dirs["ledger"]
    idempotency_key = make_idempotency_key(run_id, asset_key, prompt_data["prompt"])

    def log_event(stage: str, status: str, **kwargs):
        event = build_ledger_event(
            run_id=run_id,
            asset_key=asset_key,
            idempotency_key=idempotency_key,
            stage=stage,
            status=status,
            **kwargs,
        )
        append_ledger_event(ledger_path, event)
        return event

    print(f"--- Starting Production API Pipeline for: {asset_key} ---")
    print(f"Run ID: {run_id}")

    model_key = prompt_data.get("model", "phoenix")
    model_id = config.get("models", {}).get(model_key)
    if not model_id:
        raise ValueError(f"No model ID configured for model key '{model_key}'")

    generation_entry = find_stage_success(ledger_path, idempotency_key, "generation")
    generation_id = generation_entry.get("generation_id") if generation_entry else None
    image_url = generation_entry.get("image_url") if generation_entry else None

    if not image_url:
        log_event("generation", "started")
        try:
            leo_client = LeonardoClient()
            generation_result = leo_client.generate_and_wait(
                prompt=prompt_data["prompt"],
                model_id=model_id,
                width=prompt_data.get("width", 1024),
                height=prompt_data.get("height", 1024),
                alchemy=prompt_data.get("alchemy", True),
                return_metadata=True,
            )
            image_urls = generation_result.get("urls", [])
            if not image_urls:
                raise ApiResponseError("Leonardo generation returned no image URLs")
            image_url = image_urls[0]
            generation_id = generation_result.get("generation_id")
        except Exception as exc:
            log_event("generation", "failed", error=str(exc))
            raise
        log_event(
            "generation",
            "success",
            generation_id=generation_id,
            image_url=image_url,
            extras={"image_urls": image_urls},
        )

    raw_entry = find_stage_success(ledger_path, idempotency_key, "download_raw")
    raw_path = Path(raw_entry["local_path"]) if raw_entry and raw_entry.get("local_path") else None

    if not raw_path or not raw_path.exists():
        extension = url_extension(image_url)
        raw_path = output_dirs["raw"] / f"{asset_key}{extension}"
        log_event("download_raw", "started", image_url=image_url, local_path=str(raw_path))
        try:
            download_to_file(image_url, str(raw_path))
        except Exception as exc:
            log_event(
                "download_raw",
                "failed",
                image_url=image_url,
                local_path=str(raw_path),
                error=str(exc),
            )
            raise
        log_event("download_raw", "success", image_url=image_url, local_path=str(raw_path))

    canva_client = None
    canva_asset_id = None

    if args.sync:
        sync_entry = find_stage_success(ledger_path, idempotency_key, "sync")
        canva_asset_id = sync_entry.get("canva_asset_id") if sync_entry else None
        if not canva_asset_id:
            canva_client = CanvaClient()
            log_event("sync", "started", local_path=str(raw_path))
            try:
                folder_id = canva_client.get_or_create_shadowpunk_folder(args.canva_folder)
                upload_result = canva_client.upload_asset(
                    str(raw_path),
                    folder_id=folder_id,
                    folder_path=args.canva_folder,
                )
                canva_asset_id = upload_result["asset_id"]
            except Exception as exc:
                log_event(
                    "sync",
                    "failed",
                    local_path=str(raw_path),
                    error=str(exc),
                )
                raise
            log_event(
                "sync",
                "success",
                local_path=str(raw_path),
                canva_asset_id=canva_asset_id,
                extras={
                    "canva_folder_id": folder_id,
                    "upload_job_id": upload_result.get("job_id"),
                },
            )

    design_id = None
    if args.autofill:
        template_id = resolve_canva_template_id(config, asset_key)

        autofill_entry = find_stage_success(ledger_path, idempotency_key, "autofill")
        design_id = autofill_entry.get("design_id") if autofill_entry else None

        if not design_id:
            if canva_client is None:
                canva_client = CanvaClient()
            log_event("autofill", "started", image_url=image_url)
            try:
                autofill_job_id = canva_client.autofill_template(
                    template_id,
                    {"Background": image_url},
                )
                wait_result = canva_client.wait_for_autofill_job(autofill_job_id)
                design_id = wait_result.get("design_id")
                if not design_id:
                    raise ApiResponseError("Autofill completed without a design ID")
            except Exception as exc:
                log_event("autofill", "failed", image_url=image_url, error=str(exc))
                raise
            log_event(
                "autofill",
                "success",
                design_id=design_id,
                extras={"autofill_job_id": autofill_job_id},
            )

    export_path = None
    if args.export_format:
        export_entry = find_stage_success(ledger_path, idempotency_key, "export")
        export_path = export_entry.get("export_path") if export_entry else None
        if export_path and not Path(export_path).exists():
            export_path = None

        if not export_path:
            if canva_client is None:
                canva_client = CanvaClient()
            log_event("export", "started", design_id=design_id)
            try:
                export_job_id = canva_client.export_design(design_id, args.export_format)
                wait_result = canva_client.wait_for_export_job(export_job_id)
                urls = wait_result.get("download_urls", [])
                if not urls:
                    raise ApiResponseError("Export completed without download URLs")

                resolved_export_path = output_dirs["exports"] / f"{asset_key}_{run_id}.{args.export_format}"
                download_to_file(urls[0], str(resolved_export_path))
                export_path = str(resolved_export_path)
            except Exception as exc:
                log_event("export", "failed", design_id=design_id, error=str(exc))
                raise
            log_event(
                "export",
                "success",
                design_id=design_id,
                export_path=export_path,
                extras={"export_job_id": export_job_id, "export_url": urls[0]},
            )

    print("✅ Pipeline complete")
    print(f"Run ID: {run_id}")
    print(f"Image URL: {image_url}")
    print(f"Raw file: {raw_path}")
    if canva_asset_id:
        print(f"Canva Asset ID: {canva_asset_id}")
    if design_id:
        print(f"Canva Design ID: {design_id}")
    if export_path:
        print(f"Export file: {export_path}")
    print(f"Ledger: {ledger_path}")
    return 0


def main() -> int:
    load_environment()
    config = load_prompts()
    parser = create_parser()
    args = parser.parse_args()

    try:
        if args.command == "generate-browser":
            return run_generate_browser(args, config)
        if args.command == "generate-api":
            return run_generate_api(args, config)
        parser.error(f"Unsupported command: {args.command}")
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
