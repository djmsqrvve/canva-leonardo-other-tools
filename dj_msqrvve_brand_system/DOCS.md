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

## Notes
- `--export` requires `--autofill`.
- `generate-browser --headless` assumes the local `user_profile/` already contains a valid Leonardo login session.
- `config/prompts.yaml` ships with placeholder Canva template IDs. Put real tenant-specific IDs in `config/prompts.local.yaml` instead.
- Canva API calls can refresh expired access tokens when `CANVA_REFRESH_TOKEN`, `CANVA_CLIENT_ID`, and `CANVA_CLIENT_SECRET` are configured.
- API runs write stage-by-stage ledger entries to `outputs/ledger.jsonl`.
