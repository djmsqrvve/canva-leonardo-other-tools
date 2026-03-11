import argparse
import json
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
RATINGS_PATH = DEFAULT_OUTPUT_ROOT / "ratings.json"


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


def resolve_canva_folder(args: argparse.Namespace, prompt_data: dict | None) -> str:
    cli_folder = getattr(args, "canva_folder", DEFAULT_CANVA_FOLDER)
    if cli_folder != DEFAULT_CANVA_FOLDER:
        return cli_folder
    if prompt_data and prompt_data.get("canva_folder"):
        return prompt_data["canva_folder"]
    return cli_folder


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DJ MSQRVVE Brand System CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    browser_parser = subparsers.add_parser(
        "generate-browser",
        help="Generate assets via automated browser (Free tokens)",
    )
    browser_parser.add_argument("prompt_key", help="Key from prompts.yaml or a custom prompt string")
    browser_parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    browser_parser.add_argument("--sync", action="store_true", help="Upload generated assets to Canva")
    browser_parser.add_argument(
        "--canva-folder",
        default=DEFAULT_CANVA_FOLDER,
        help=f"Target Canva folder path for sync (default: {DEFAULT_CANVA_FOLDER})",
    )

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

    batch_parser = subparsers.add_parser(
        "generate-batch",
        help="Generate multiple assets in one run",
    )
    batch_parser.add_argument("prompt_key", nargs="?", default=None, help="Single key for variant mode")
    batch_parser.add_argument("--category", help="Generate all prompts in a category")
    batch_parser.add_argument("--all", action="store_true", dest="all_prompts", help="Generate all prompts")
    batch_parser.add_argument("--variants", type=int, default=1, help="Variants per prompt (default: 1)")
    batch_parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    batch_parser.add_argument("--sync", action="store_true", help="Upload generated assets to Canva")
    batch_parser.add_argument(
        "--canva-folder",
        default=DEFAULT_CANVA_FOLDER,
        help=f"Target Canva folder path for sync (default: {DEFAULT_CANVA_FOLDER})",
    )

    subparsers.add_parser("canva-auth", help="Check Canva authentication status")

    gallery_parser = subparsers.add_parser("gallery", help="Launch asset gallery UI")
    gallery_parser.add_argument("--port", type=int, default=6868, help="Port (default: 6868)")

    subparsers.add_parser("suggest", help="Suggest next generations based on ratings")

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


def run_generate_browser(args: argparse.Namespace, config: dict, *, browser=None) -> int:
    prompt_data = config.get("prompts", {}).get(args.prompt_key, {})
    prompt = prompt_data.get("prompt", args.prompt_key)
    asset_key = args.prompt_key if args.prompt_key in config.get("prompts", {}) else "custom"
    canva_folder = resolve_canva_folder(args, prompt_data)

    print("--- Starting Browser Automation Pipeline ---")
    owns_browser = browser is None
    if owns_browser:
        browser = create_leonardo_browser(headless=args.headless)
    try:
        browser.login()

        run_id = generate_run_id()
        output_dirs = ensure_output_dirs(str(DEFAULT_OUTPUT_ROOT), run_id)
        ledger_path = output_dirs["ledger"]
        idempotency_key = make_idempotency_key(run_id, asset_key, prompt)

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

        log_event("generation", "started")
        image_urls = browser.generate(prompt)
        if not image_urls:
            log_event("generation", "failed", error="No images found")
            print("Generation failed or no images found.")
            return 1

        log_event("generation", "success", extras={"image_urls": image_urls})
        print(f"Generated {len(image_urls)} images")

        downloaded: list[Path] = []
        for index, url in enumerate(image_urls):
            ext = url_extension(url)
            local_path = output_dirs["raw"] / f"browser_{index}{ext}"
            try:
                download_to_file(url, str(local_path))
                downloaded.append(local_path)
                log_event("download_raw", "success", image_url=url, local_path=str(local_path))
                print(f"   Downloaded [{index}] -> {local_path}")
            except Exception as exc:
                log_event("download_raw", "failed", image_url=url, error=str(exc))
                print(f"   Download [{index}] failed: {exc}")

        if not downloaded:
            print("All downloads failed.")
            return 1

        if args.sync:
            print(f"Syncing {len(downloaded)} images to Canva folder: {canva_folder}")
            canva_client = CanvaClient()
            folder_id = canva_client.get_or_create_shadowpunk_folder(canva_folder)
            for local_path in downloaded:
                try:
                    result = canva_client.upload_asset(
                        str(local_path),
                        folder_id=folder_id,
                        folder_path=canva_folder,
                    )
                    log_event(
                        "sync", "success",
                        local_path=str(local_path),
                        canva_asset_id=result["asset_id"],
                    )
                    print(f"   Uploaded {local_path.name} -> Canva asset {result['asset_id']}")
                except Exception as exc:
                    log_event("sync", "failed", local_path=str(local_path), error=str(exc))
                    print(f"   Upload {local_path.name} failed: {exc}")

        print(f"Pipeline complete (run_id: {run_id})")
        print(f"Raw output: {output_dirs['raw']}")
        return 0
    finally:
        if owns_browser:
            print("Closing browser...")
            browser.close()


def run_generate_api(args: argparse.Namespace, config: dict) -> int:
    asset_key = args.asset_type
    prompt_data = config.get("prompts", {}).get(asset_key)
    if not prompt_data:
        raise ValueError(f"No prompt configuration found for '{asset_key}' in prompts.yaml")

    if args.export_format and not args.autofill:
        raise ValueError("--export requires --autofill to produce a design to export")

    canva_folder = resolve_canva_folder(args, prompt_data)
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

    current_stage = "config"

    def print_failure_context() -> None:
        print(f"API pipeline failed at stage: {current_stage}")
        print(f"Run ID: {run_id} | Ledger: {ledger_path}")

    model_key = prompt_data.get("model", "phoenix")
    model_id = config.get("models", {}).get(model_key)
    if not model_id:
        raise ValueError(f"No model ID configured for model key '{model_key}'")

    try:
        current_stage = "generation"
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

        current_stage = "download_raw"
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
            current_stage = "sync"
            sync_entry = find_stage_success(ledger_path, idempotency_key, "sync")
            canva_asset_id = sync_entry.get("canva_asset_id") if sync_entry else None
            if not canva_asset_id:
                canva_client = CanvaClient()
                log_event("sync", "started", local_path=str(raw_path))
                try:
                    folder_id = canva_client.get_or_create_shadowpunk_folder(canva_folder)
                    upload_result = canva_client.upload_asset(
                        str(raw_path),
                        folder_id=folder_id,
                        folder_path=canva_folder,
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
            current_stage = "autofill"
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
            current_stage = "export"
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
    except Exception:
        print_failure_context()
        raise

    print("Pipeline complete")
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


def run_generate_batch(args: argparse.Namespace, config: dict) -> int:
    prompts = config.get("prompts", {})

    if args.prompt_key:
        if args.prompt_key not in prompts:
            raise ValueError(f"Unknown prompt key: '{args.prompt_key}'")
        keys = [args.prompt_key]
    elif args.category:
        keys = [k for k, v in prompts.items() if v.get("category") == args.category]
        if not keys:
            raise ValueError(f"No prompts found for category: '{args.category}'")
    elif args.all_prompts:
        keys = list(prompts.keys())
    else:
        raise ValueError("Specify a prompt_key, --category, or --all")

    total = len(keys) * args.variants
    print(f"--- Batch: {len(keys)} prompt(s) x {args.variants} variant(s) = {total} generation(s) ---")

    browser = create_leonardo_browser(headless=args.headless)
    results = []
    try:
        for key in keys:
            for v in range(args.variants):
                label = f"{key}" if args.variants == 1 else f"{key} (variant {v + 1})"
                print(f"\n[{len(results) + 1}/{total}] {label}")
                batch_args = argparse.Namespace(
                    prompt_key=key,
                    headless=args.headless,
                    sync=args.sync,
                    canva_folder=args.canva_folder,
                )
                try:
                    rc = run_generate_browser(batch_args, config, browser=browser)
                    results.append((label, "OK" if rc == 0 else "FAIL"))
                except Exception as exc:
                    print(f"   Error: {exc}")
                    results.append((label, f"ERROR: {exc}"))
    finally:
        print("\nClosing browser...")
        browser.close()

    print("\n--- Batch Summary ---")
    for label, status in results:
        print(f"  {label}: {status}")
    failures = sum(1 for _, s in results if s != "OK")
    return 1 if failures else 0


def run_canva_auth_check() -> int:
    print("Checking Canva authentication...")
    token = os.environ.get("CANVA_ACCESS_TOKEN")
    if not token:
        print("CANVA_ACCESS_TOKEN not set in .env")
        return 1

    import requests
    resp = requests.get(
        "https://api.canva.com/rest/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    if resp.status_code == 200:
        user = resp.json()
        user_id = user.get("team_user", {}).get("user_id", "unknown")
        print(f"Canva auth OK (user: {user_id})")
        return 0

    if resp.status_code in (401, 403):
        print(f"Token expired ({resp.status_code}). Attempting refresh...")
        try:
            canva = CanvaClient()
            canva.token_manager.refresh_access_token()
            print("Token refreshed successfully.")
            return 0
        except Exception as exc:
            print(f"Refresh failed: {exc}")
            print("Re-run: python src/auth_server.py")
            return 1

    print(f"Unexpected response: {resp.status_code} {resp.text[:200]}")
    return 1


def run_gallery(args: argparse.Namespace) -> int:
    from gallery import create_gallery_app
    app = create_gallery_app()
    print(f"Gallery running at http://127.0.0.1:{args.port}")
    app.run(host="127.0.0.1", port=args.port, debug=False)
    return 0


def load_ratings() -> dict:
    if RATINGS_PATH.exists():
        return json.loads(RATINGS_PATH.read_text(encoding="utf-8"))
    return {}


def run_suggest(config: dict) -> int:
    prompts = config.get("prompts", {})
    ratings = load_ratings()
    ledger_path = DEFAULT_OUTPUT_ROOT / "ledger.jsonl"

    generated_keys: set[str] = set()
    if ledger_path.exists():
        with ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("stage") == "generation" and event.get("status") == "success":
                    generated_keys.add(event.get("asset_key", ""))

    categories: dict[str, list[str]] = {}
    for key, data in prompts.items():
        cat = data.get("category", "uncategorized")
        categories.setdefault(cat, []).append(key)

    favorites = {k: v for k, v in ratings.items() if v.get("favorite")}
    top_rated = sorted(
        ((k, v.get("rating", 0)) for k, v in ratings.items() if v.get("rating")),
        key=lambda x: x[1],
        reverse=True,
    )

    print("--- Suggestions ---\n")

    if favorites:
        print(f"Favorites ({len(favorites)}):")
        for key in list(favorites)[:5]:
            print(f"  {key}")
        print(f"\nRe-roll favorites: python -m main generate-batch --regen-favorites --variants 3 --headless\n")

    if top_rated:
        print("Top rated:")
        for key, rating in top_rated[:5]:
            print(f"  {key} ({rating}/5)")
        print()

    missing = set(prompts.keys()) - generated_keys
    if missing:
        print(f"Not yet generated ({len(missing)}):")
        for key in sorted(missing):
            cat = prompts[key].get("category", "?")
            print(f"  {key} [{cat}]")
        by_cat = {}
        for key in missing:
            cat = prompts[key].get("category", "uncategorized")
            by_cat.setdefault(cat, []).append(key)
        for cat in sorted(by_cat):
            print(f"\n  Generate {cat}: python -m main generate-batch --category {cat} --headless")
    else:
        print("All prompt keys have been generated at least once.")

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
        if args.command == "generate-batch":
            return run_generate_batch(args, config)
        if args.command == "canva-auth":
            return run_canva_auth_check()
        if args.command == "gallery":
            return run_gallery(args)
        if args.command == "suggest":
            return run_suggest(config)
        parser.error(f"Unsupported command: {args.command}")
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
