# Operations Runbook

## Environment Setup
1. Create a virtual environment in `dj_msqrvve_brand_system/`.
2. Install `requirements-dev.txt`.
3. Install `requirements-browser.txt` only if you need browser automation.
4. Copy `.env.example` to `.env` and fill the keys for the workflows you will use.

## Validation Tiers
- `make health` is the fast local validation path: Python tests plus a CLI help smoke check.
- `make full-check` extends `make health` with dashboard lint, dashboard tests, and a production `next build`.
- `python src/test_health.py` is the supported manual live-provider auth check for Leonardo and Canva.
- `python src/test_health.py smoke-plan --asset-key <asset_key>` prints the supported live smoke sequence and local readiness state.
- There is no CI-managed live-provider suite. External-provider smoke runs remain manual because they require tenant credentials, real Canva template IDs, and can create provider-side artifacts.

## Canva Auth Bootstrap
Run:
```bash
cd dj_msqrvve_brand_system
python src/auth_server.py
```

Notes:
- `CANVA_CLIENT_ID` and `CANVA_CLIENT_SECRET` must be set first.
- `CANVA_INCLUDE_AUTOFILL_SCOPES=1` adds brand-template scopes for autofill/export use cases.
- If Canva returns a refresh token, the helper writes it to `CANVA_REFRESH_TOKEN`.

## Canva Token Refresh
- Canva runtime calls use `CANVA_ACCESS_TOKEN` first.
- If a Canva request returns `401` or `403` and `CANVA_REFRESH_TOKEN`, `CANVA_CLIENT_ID`, and `CANVA_CLIENT_SECRET` are set, the client refreshes once and retries the request.
- Refreshed access tokens are written back to `dj_msqrvve_brand_system/.env` when that file exists locally.
- If Canva rotates the refresh token, the new `CANVA_REFRESH_TOKEN` is persisted. If Canva omits a new refresh token, the existing one is kept.

## Canva Template Overrides
Autofill and export remain tenant-specific. Keep real Canva template IDs out of the public sample config.

Operator setup:
```bash
cd dj_msqrvve_brand_system
cp config/prompts.local.example.yaml config/prompts.local.yaml
```

Notes:
- `config/prompts.yaml` is the public sample config and intentionally keeps `TEMPLATE_ID_HERE` placeholders.
- `config/prompts.local.yaml` is gitignored and only supports `canva_templates` overrides.
- The CLI merges `config/prompts.local.yaml` over the public sample at runtime.
- `--autofill` and `--export` fail fast when a template mapping is missing, blank, or still set to `TEMPLATE_ID_HERE`.

## Browser Automation Bootstrap
Dashboard browser jobs run headless and expect an existing logged-in Chrome profile.

Bootstrap the profile once with an interactive run:
```bash
cd dj_msqrvve_brand_system
python src/main.py generate-browser "your prompt"
```

If Chrome is not on `PATH`, set `CHROME_BINARY` in the shell before running the command.

Notes:
- `generate-browser --headless` is only supported after the interactive bootstrap has already populated `user_profile/`.
- If Leonardo redirects back to login or reports an expired saved session, rerun `python src/main.py generate-browser "your prompt"` without `--headless` to refresh the profile.
- Browser failures write artifacts to `dj_msqrvve_brand_system/outputs/browser-artifacts/<timestamp>-<phase>/` with a screenshot, page dump, and metadata when available.

## Browser Automation Smoke And Maintenance
Supported smoke procedure:
1. Run one interactive `generate-browser` command if the saved session is missing or expired.
2. Run a headless smoke check with a short prompt:
```bash
cd dj_msqrvve_brand_system
python src/main.py generate-browser "simple lighting smoke prompt" --headless
```
3. If the smoke check fails, inspect the newest directory under `outputs/browser-artifacts/` to see whether the issue was a login redirect, missing selector, or stalled result detection.
4. If Leonardo changed its UI, update the selectors or readiness checks in `src/lib/leonardo_browser.py` and rerun `make health` and `make full-check`.

## Live Provider Smoke Procedure
Start with a local readiness summary:
```bash
cd dj_msqrvve_brand_system
python src/test_health.py state --asset-key social_banner_bg
python src/test_health.py auth
python src/test_health.py smoke-plan --asset-key social_banner_bg
```

Supported manual smoke sequence:
1. Leonardo API auth:
```bash
cd dj_msqrvve_brand_system
python src/test_health.py auth --check leonardo
```
2. Canva auth and refresh readiness:
```bash
python src/test_health.py auth --check canva
```
3. Leonardo API generation smoke:
```bash
python src/main.py generate-api social_banner_bg --run-id smoke-social-banner-bg-api-<timestamp>
```
4. Canva sync smoke:
```bash
python src/main.py generate-api social_banner_bg --sync --canva-folder "Shadowpunk/Generations" --run-id smoke-social-banner-bg-sync-<timestamp>
```
5. Canva autofill and export smoke after real private template IDs are configured:
```bash
python src/main.py generate-api social_banner_bg --autofill --export png --run-id smoke-social-banner-bg-export-<timestamp>
```
6. Browser smoke:
   Run the interactive bootstrap if the saved session is missing or expired.
   Then run `python src/main.py generate-browser "simple lighting smoke prompt" --headless`.
7. Dashboard restart recovery smoke:
   Start `npm run dev` in `dashboard/`.
   Queue a job until it reaches `running`.
   Stop the dashboard process.
   Restart `npm run dev`.
   Confirm the interrupted job is surfaced as `failed` with a restart-specific error and can be retried.

Failure diagnostics to inspect during live smoke:
- API pipeline failures print the run ID, failed stage, ledger path, and output directories.
- API run history is appended to `dj_msqrvve_brand_system/outputs/ledger.jsonl`.
- Browser failures write artifacts under `dj_msqrvve_brand_system/outputs/browser-artifacts/`.
- Dashboard restart behavior is persisted in `dj_msqrvve_brand_system/outputs/dashboard-jobs.json`.

## Validation Commands
From repo root:
```bash
make health
make full-check
```

These commands are the supported validation contract for local work and CI.

## Dashboard Runtime
- `npm run dev` and `npm start` in `dashboard/` bind to `127.0.0.1:6767`.
- Supported dashboard execution uses the queue-backed `/api/jobs` routes; the legacy direct execution route is not part of the supported surface.
- Dashboard API requests are rejected when the request host, origin, or forwarded client address is not loopback-local.

## State and Recovery
- API run ledger: `dj_msqrvve_brand_system/outputs/ledger.jsonl`
- Dashboard queue state: `dj_msqrvve_brand_system/outputs/dashboard-jobs.json`

Recovery behavior:
- API retries can reuse finished stages through the ledger when the same run ID is supplied.
- Dashboard restarts keep queued jobs and fail previously running jobs with a restart-specific message.

## Limits
- Browser jobs do not currently write ledger history.
- The dashboard queue is single-process and local-first.
- Canva autofill/export remains tenant-specific until real template IDs are added to `config/prompts.local.yaml`.
