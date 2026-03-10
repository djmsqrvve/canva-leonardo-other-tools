# Operations And Validation

## Local Setup
Python:
```bash
cd dj_msqrvve_brand_system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

Optional browser support:
```bash
pip install -r requirements-browser.txt
```

Dashboard:
```bash
cd ../dashboard
npm install
```

## Core Environment Variables
- `LEONARDO_API_KEY`: required for `generate-api` — not currently provisioned; use `generate-browser` instead
- `CANVA_CLIENT_ID`, `CANVA_CLIENT_SECRET`: required for Canva OAuth bootstrap and refresh
- `CANVA_ACCESS_TOKEN`: required for Canva sync/autofill/export unless refresh flow can mint a new access token
- `CANVA_REFRESH_TOKEN`: optional but recommended for Canva token renewal
- `CANVA_INCLUDE_AUTOFILL_SCOPES=1`: include brand-template scopes when bootstrapping Canva auth
- `FIREFOX_BINARY`: optional local Firefox override for browser mode

## Validation Tiers
- `make health`: Python tests plus CLI help smoke check
- `make full-check`: `make health` plus dashboard lint, tests, and production build
- `python src/test_health.py`: manual live-provider auth checks
- `python src/test_health.py state --asset-key <asset_key>`: local readiness summary
- `python src/test_health.py smoke-plan --asset-key <asset_key>`: supported live smoke sequence

## Local State Files
- `dj_msqrvve_brand_system/outputs/ledger.jsonl`
- `dj_msqrvve_brand_system/outputs/dashboard-jobs.json`
- `dj_msqrvve_brand_system/outputs/browser-artifacts/`
- `dj_msqrvve_brand_system/user_profile/`
- `dj_msqrvve_brand_system/config/prompts.local.yaml`

## Live Smoke Workflow
Start with:
```bash
cd dj_msqrvve_brand_system
./venv/bin/python src/test_health.py auth
./venv/bin/python src/test_health.py smoke-plan --asset-key social_banner_bg
```

Leonardo will show `[BLOCKED]` (expected — no API key). Canva `[OK]` is the
meaningful signal.

Supported manual smoke sequence:
1. Canva auth and refresh readiness
2. Browser bootstrap (interactive, one-time) — run `generate-browser` without `--headless` to seed `user_profile/`
3. Headless browser smoke — `generate-browser --headless`
4. Canva sync (after raw asset is in `outputs/`)
5. Canva autofill and export after private template IDs exist
6. Dashboard restart recovery
7. (Future) Leonardo API generation — blocked until `LEONARDO_API_KEY` is provisioned

## Restart Recovery Expectations
- Dashboard queued jobs persist across restart.
- Dashboard running jobs are converted to failed/retryable on restart.
- API retries can reuse completed ledger stages when the same run ID is supplied.

## Failure Triage
- API pipeline failures print run ID, failed stage, ledger path, and output directories.
- Browser failures write screenshot, HTML, and metadata artifacts under `outputs/browser-artifacts/`.
- Dashboard issues should be checked against `outputs/dashboard-jobs.json` and dashboard test coverage.

## Public Vs Private Config
- Keep `config/prompts.yaml` public and placeholder-safe.
- Put real `canva_templates` values in `config/prompts.local.yaml`.
- Do not commit tenant secrets, real Canva template IDs, or private credentials.

## Event Integration Boundary

This repo owns the Canva and Leonardo runtime surface. It does not own the full
MSQRVVE Madness event operating system.

Cross-repo dependency:

- event workspace:
  `/home/dj/dev/brand/stream/events/msqrvve_madness_march_subathon_2026`
- key event-side docs:
  - `handoff/HANDOFF_PROJECT_CANVA_ASSET_PRODUCTION.md`
  - `operations/CANVA_TEMPLATE_API_403_2026-03-08.md`
  - `operations/CANVA_TEMPLATE_ID_REGISTRY_DAY02.md`

Use this repo for generation/auth/runtime truth and the event workspace for
launch readiness, blockers, and staged-asset coordination.
