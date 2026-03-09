# Operations Runbook

## Environment Setup
1. Create a virtual environment in `dj_msqrvve_brand_system/`.
2. Install `requirements-dev.txt`.
3. Install `requirements-browser.txt` only if you need browser automation.
4. Copy `.env.example` to `.env` and fill the keys for the workflows you will use.

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

## Browser Automation Bootstrap
Dashboard browser jobs run headless and expect an existing logged-in Chrome profile.

Bootstrap the profile once with an interactive run:
```bash
cd dj_msqrvve_brand_system
python src/main.py generate-browser "your prompt"
```

If Chrome is not on `PATH`, set `CHROME_BINARY` in the shell before running the command.

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
- Canva autofill/export remains tenant-specific until real template IDs replace `TEMPLATE_ID_HERE` in `config/prompts.yaml`.
