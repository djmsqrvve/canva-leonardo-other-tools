"""Lightweight gallery server for browsing, rating, and comparing generated assets."""
from __future__ import annotations

import json
from pathlib import Path

import yaml
from flask import Flask, jsonify, request, send_file, send_from_directory

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ROOT = PROJECT_ROOT / "outputs"
LEDGER_PATH = OUTPUT_ROOT / "ledger.jsonl"
RATINGS_PATH = OUTPUT_ROOT / "ratings.json"
PROMPTS_PATH = PROJECT_ROOT / "config" / "prompts.yaml"
GALLERY_UI_DIR = Path(__file__).resolve().parent / "gallery_ui"


def load_ratings() -> dict:
    if RATINGS_PATH.exists():
        return json.loads(RATINGS_PATH.read_text(encoding="utf-8"))
    return {}


def save_ratings(ratings: dict) -> None:
    RATINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RATINGS_PATH.write_text(json.dumps(ratings, indent=2), encoding="utf-8")


def load_prompts_config() -> dict:
    if PROMPTS_PATH.exists():
        with PROMPTS_PATH.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def scan_assets() -> list[dict]:
    """Build asset list from ledger + raw file scan."""
    assets = []
    seen_files: set[str] = set()
    config = load_prompts_config()
    prompts = config.get("prompts", {})
    ratings = load_ratings()

    if LEDGER_PATH.exists():
        with LEDGER_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("stage") == "download_raw" and event.get("status") == "success":
                    local_path = event.get("local_path", "")
                    if local_path and Path(local_path).exists():
                        p = Path(local_path)
                        run_id = event.get("run_id", p.parent.name)
                        asset_key = event.get("asset_key", "unknown")
                        prompt_data = prompts.get(asset_key, {})
                        file_key = f"{run_id}/{p.name}"
                        rating_data = ratings.get(file_key, {})
                        assets.append({
                            "run_id": run_id,
                            "filename": p.name,
                            "asset_key": asset_key,
                            "category": prompt_data.get("category", "uncategorized"),
                            "timestamp": event.get("timestamp", ""),
                            "image_url": f"/api/assets/{run_id}/{p.name}",
                            "rating": rating_data.get("rating"),
                            "favorite": rating_data.get("favorite", False),
                        })
                        seen_files.add(str(p))

    raw_root = OUTPUT_ROOT / "raw"
    if raw_root.is_dir():
        for run_dir in sorted(raw_root.iterdir(), reverse=True):
            if not run_dir.is_dir():
                continue
            for img in sorted(run_dir.iterdir()):
                if img.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
                    continue
                if str(img) in seen_files:
                    continue
                file_key = f"{run_dir.name}/{img.name}"
                rating_data = ratings.get(file_key, {})
                assets.append({
                    "run_id": run_dir.name,
                    "filename": img.name,
                    "asset_key": "unknown",
                    "category": "uncategorized",
                    "timestamp": "",
                    "image_url": f"/api/assets/{run_dir.name}/{img.name}",
                    "rating": rating_data.get("rating"),
                    "favorite": rating_data.get("favorite", False),
                })

    return assets


def create_gallery_app() -> Flask:
    app = Flask(__name__, static_folder=None)

    @app.route("/")
    def index():
        return send_from_directory(str(GALLERY_UI_DIR), "index.html")

    @app.route("/api/assets")
    def list_assets():
        assets = scan_assets()
        category = request.args.get("category")
        asset_key = request.args.get("asset_key")
        favorites_only = request.args.get("favorites") == "true"
        if category:
            assets = [a for a in assets if a["category"] == category]
        if asset_key:
            assets = [a for a in assets if a["asset_key"] == asset_key]
        if favorites_only:
            assets = [a for a in assets if a.get("favorite")]
        return jsonify(assets)

    @app.route("/api/assets/<run_id>/<filename>")
    def serve_asset(run_id, filename):
        file_path = OUTPUT_ROOT / "raw" / run_id / filename
        if not file_path.exists():
            return "Not found", 404
        return send_file(str(file_path))

    @app.route("/api/assets/<run_id>/<filename>/rate", methods=["POST"])
    def rate_asset(run_id, filename):
        ratings = load_ratings()
        key = f"{run_id}/{filename}"
        data = request.get_json(force=True)
        if key not in ratings:
            ratings[key] = {}
        if "rating" in data:
            ratings[key]["rating"] = max(1, min(5, int(data["rating"])))
        if "favorite" in data:
            ratings[key]["favorite"] = bool(data["favorite"])
        save_ratings(ratings)
        return jsonify(ratings[key])

    @app.route("/api/categories")
    def list_categories():
        config = load_prompts_config()
        prompts = config.get("prompts", {})
        cats = sorted(set(v.get("category", "uncategorized") for v in prompts.values()))
        return jsonify(cats)

    return app
