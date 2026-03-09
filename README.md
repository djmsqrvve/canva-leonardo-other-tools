[![CI](https://github.com/djmsqrvve/canva-leonardo-other-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/djmsqrvve/canva-leonardo-other-tools/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

# Twilight Shadowpunk Asset Pipeline

Local-first automation for generating Leonardo imagery, syncing assets into Canva, and monitoring jobs from a Next.js dashboard.

## What Is Supported
- Python CLI for Leonardo API generation, Canva sync, Canva autofill, and Canva export.
- Local browser automation for Leonardo web generation after an interactive login bootstrap.
- Next.js dashboard for queueing jobs, monitoring status, and reviewing ledger-backed history.

## Quick Start
### 1. Install Python dependencies
```bash
cd dj_msqrvve_brand_system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

Optional browser automation dependencies:
```bash
pip install -r requirements-browser.txt
```

### 2. Configure environment
```bash
cp .env.example .env
```

Set the keys you need:
- `LEONARDO_API_KEY` for `generate-api`
- `CANVA_CLIENT_ID` and `CANVA_CLIENT_SECRET` for local Canva OAuth bootstrap and token refresh
- `CANVA_ACCESS_TOKEN` for Canva sync/autofill/export
- `CANVA_REFRESH_TOKEN` if you want the runtime to auto-renew expired Canva access tokens
- `CANVA_INCLUDE_AUTOFILL_SCOPES=1` if you want the auth helper to request brand-template scopes

If `CANVA_REFRESH_TOKEN`, `CANVA_CLIENT_ID`, and `CANVA_CLIENT_SECRET` are set, Canva API calls retry once on `401` or `403` by refreshing the access token. Refreshed values are written back to `dj_msqrvve_brand_system/.env` when that file exists.

### 3. Bootstrap Canva auth when needed
```bash
python src/auth_server.py
```

The auth helper saves `CANVA_ACCESS_TOKEN` and, when Canva returns one, `CANVA_REFRESH_TOKEN`.

If you plan to use Canva autofill or export, keep tenant-specific template IDs in a local override file:
```bash
cp config/prompts.local.example.yaml config/prompts.local.yaml
```

`config/prompts.local.yaml` is gitignored. Public `config/prompts.yaml` intentionally keeps placeholder `canva_templates` values.

### 4. Validate the repo
```bash
cd ..
make health
make full-check
```

Automated validation remains local and mostly mocked. For live-provider readiness, use:
```bash
cd dj_msqrvve_brand_system
python src/test_health.py
python src/test_health.py smoke-plan --asset-key social_banner_bg
```

### 5. Start the dashboard
```bash
cd dashboard
npm install
npm run dev
```

The dashboard binds to `127.0.0.1:6767`. Supported dashboard execution goes through the queue-backed `/api/jobs` routes only.

## Validation Tiers
- `make health`: Python unit tests plus a CLI help smoke check.
- `make full-check`: `make health` plus dashboard lint, tests, and production build.
- `python src/test_health.py`: manual live-provider auth checks against Leonardo and Canva.
- `python src/test_health.py smoke-plan --asset-key <asset_key>`: local readiness summary plus the supported live smoke commands for Leonardo API, Canva sync/autofill/export, browser checks, and dashboard restart recovery.

## Workflow Matrix
| Workflow | Requirements | Notes |
| --- | --- | --- |
| `generate-api` | `LEONARDO_API_KEY` | Stable production path |
| `generate-api --sync` | `LEONARDO_API_KEY`, Canva access token or refresh-capable OAuth config | Uploads raw output to Canva |
| `generate-api --autofill --export` | `LEONARDO_API_KEY`, Canva access token or refresh-capable OAuth config, private `canva_templates` IDs in `config/prompts.local.yaml` | Public placeholder mappings are rejected |
| `generate-browser` | `requirements-browser.txt`, local Chrome/Chromium | First login must be interactive; failures write local browser artifacts |
| Dashboard browser jobs | Bootstrapped `user_profile/` | Dashboard browser jobs run headless, fail fast until the profile is seeded, and require an interactive re-bootstrap if the saved session expires |

## CLI Examples
Works after clone once the matching credentials are configured:
```bash
cd dj_msqrvve_brand_system
python src/main.py generate-api social_banner_bg
python src/main.py generate-api social_banner_bg --sync --canva-folder "Shadowpunk/Generations"
python src/main.py generate-browser "Twilight shadowpunk skyline with negative space"
```

If Leonardo reports that the saved session expired, rerun `generate-browser` without `--headless` once to refresh `user_profile/`.

Requires private Canva template IDs in `config/prompts.local.yaml`:
```bash
python src/main.py generate-api madness_launch_key_art --autofill --export png
```

## Outputs and State
- Raw downloads: `dj_msqrvve_brand_system/outputs/raw/<run_id>/`
- Canva exports: `dj_msqrvve_brand_system/outputs/exports/<run_id>/`
- API ledger: `dj_msqrvve_brand_system/outputs/ledger.jsonl`
- Browser failure artifacts: `dj_msqrvve_brand_system/outputs/browser-artifacts/<timestamp>-<phase>/`
- Dashboard queue state: `dj_msqrvve_brand_system/outputs/dashboard-jobs.json`

If the dashboard restarts, queued jobs are restored and previously running jobs are marked failed with a restart-specific error so they can be retried safely.

## Repo Map
- `dj_msqrvve_brand_system/` - active Python CLI, API clients, auth helper, tests
- `dashboard/` - active Next.js dashboard and API routes
- `docs/` - active architecture and operations docs
- `docs/archive/` - historical planning, sprint, and handoff material
- `archive/` - archived prototype/scaffold code
- `assets/`, `game_assets/`, `stream_ops/`, `shared/`, `bevy_project/`, `pipeline_scripts/` - reference assets or adjacent project material

## Known Limitations
- The dashboard queue is intentionally local-first and single-process; it is not a distributed worker system.
- The dashboard API is intentionally localhost-only and binds to `127.0.0.1` by default.
- Browser automation depends on Leonardo UI selectors and a locally bootstrapped Chrome profile. When the saved session expires or a selector breaks, inspect `outputs/browser-artifacts/` and refresh the profile with an interactive `generate-browser` run.
- Ledger history reflects API runs; browser jobs remain queue-tracked but do not write the API ledger.
- There is no separate automated live-provider integration suite in CI. Provider auth and end-to-end smoke checks stay manual through `src/test_health.py` and the operations runbook.

## Docs
- [Architecture](docs/ARCHITECTURE.md)
- [Operations](docs/OPERATIONS.md)
- [Python CLI Notes](dj_msqrvve_brand_system/DOCS.md)
- [Contributing](CONTRIBUTING.md)
- [Archived historical docs](docs/archive/README.md)
