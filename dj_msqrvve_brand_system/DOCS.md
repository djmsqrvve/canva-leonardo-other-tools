# Python CLI Notes

## Supported Entry Points
- `src/main.py` is the maintained CLI.
- `src/auth_server.py` is the local Canva OAuth bootstrap helper.
- `src/cli.py` remains only as a deprecated compatibility scaffold.

## Install Profiles
```bash
pip install -r requirements-dev.txt
```

Optional browser support:
```bash
pip install -r requirements-browser.txt
```

## Common Commands
Production API generation:
```bash
python src/main.py generate-api social_banner_bg
python src/main.py generate-api social_banner_bg --sync
```

Browser generation bootstrap:
```bash
python src/main.py generate-browser "your prompt"
```

Autofill and export after real template IDs are configured:
```bash
python src/main.py generate-api madness_launch_key_art --autofill --export png
```

Manual live-provider checks:
```bash
python src/test_health.py
python src/test_health.py smoke-plan --asset-key social_banner_bg
```

## Notes
- `--export` requires `--autofill`.
- `generate-browser --headless` assumes the local `user_profile/` already contains a valid Leonardo login session.
- If the saved Leonardo session expires, rerun `python src/main.py generate-browser "your prompt"` without `--headless` once to refresh `user_profile/`.
- Browser automation failures write local artifacts to `outputs/browser-artifacts/` when a screenshot, page dump, or selector context can be captured.
- `config/prompts.yaml` ships with placeholder Canva template IDs. Put real tenant-specific IDs in `config/prompts.local.yaml` instead.
- Canva API calls can refresh expired access tokens when `CANVA_REFRESH_TOKEN`, `CANVA_CLIENT_ID`, and `CANVA_CLIENT_SECRET` are configured.
- API runs write stage-by-stage ledger entries to `outputs/ledger.jsonl`.
- API failures also print the run ID, failed stage, ledger path, and output directories to make live debugging faster.
