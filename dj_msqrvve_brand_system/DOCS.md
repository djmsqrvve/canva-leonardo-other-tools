# Python CLI Notes

## Supported Entry Points
- `src/main.py` is the maintained CLI.
- `src/auth_server.py` is the local Canva OAuth bootstrap helper.

## Install Profiles
```bash
pip install -r requirements-dev.txt
```

Optional browser support:
```bash
pip install -r requirements-browser.txt
```

## Common Commands
All via `PYTHONPATH=src venv/bin/python -m main`:

```bash
# Production API generation
generate-api social_banner_bg
generate-api social_banner_bg --sync

# Browser generation (first run interactive, then headless)
generate-browser "your prompt"
generate-browser social_banner_bg --headless --sync

# Batch generation
generate-batch --category social --headless
generate-batch --all --headless
generate-batch social_banner_bg --variants 3 --headless

# Canva token check/refresh
canva-auth

# Asset gallery (browse, rate, compare)
gallery --port 6868

# Suggest next generations
suggest

# Autofill and export (requires real template IDs in prompts.local.yaml)
generate-api madness_launch_key_art --autofill --export png
```

Manual live-provider checks:
```bash
python src/test_health.py
python src/test_health.py smoke-plan --asset-key social_banner_bg
```

## Notes
- `--export` requires `--autofill`.
- `generate-browser --headless` assumes the local `user_profile/` already contains a valid Leonardo login session.
- If the saved Leonardo session expires, rerun without `--headless` once to refresh `user_profile/`.
- Browser automation failures write local artifacts to `outputs/browser-artifacts/`.
- `config/prompts.yaml` ships with placeholder Canva template IDs. Put real tenant-specific IDs in `config/prompts.local.yaml` instead.
- All prompts have `category` and `canva_folder` fields for batch generation and per-prompt Canva folder routing.
- Canva API calls can refresh expired access tokens when `CANVA_REFRESH_TOKEN`, `CANVA_CLIENT_ID`, and `CANVA_CLIENT_SECRET` are configured.
- Both API and browser paths write stage-by-stage ledger entries to `outputs/ledger.jsonl`.
- Gallery ratings persist to `outputs/ratings.json`.
- Failures print the run ID, failed stage, ledger path, and output directories for debugging.
