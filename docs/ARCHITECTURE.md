# Architecture Overview

## Primary Components
- `dj_msqrvve_brand_system/` is the supported automation engine.
- `dashboard/` is the supported local control plane.
- `docs/archive/` and `archive/` hold historical material that is not part of the supported runtime.

## Python CLI Flow
`src/main.py` is the entrypoint for two local-first modes:
- `generate-api` uses the Leonardo API, downloads the result, optionally uploads to Canva, optionally autofills a template, and optionally exports the finished design.
- `generate-browser` drives the Leonardo web UI through Selenium using a persistent local Chrome profile.

The API path writes a JSONL ledger under `outputs/ledger.jsonl`. Ledger entries are keyed by a run ID plus prompt hash so completed stages can be reused on retries.

Canva API modules share one token manager. If `CANVA_REFRESH_TOKEN`, `CANVA_CLIENT_ID`, and `CANVA_CLIENT_SECRET` are configured, expired Canva access tokens are refreshed in-process and retried once.

## Dashboard Flow
The dashboard submits jobs to Next.js route handlers, which spawn the Python CLI. Jobs are persisted to `dj_msqrvve_brand_system/outputs/dashboard-jobs.json`.

Supported execution is queue-based through `/api/jobs` and related job-control routes. The dashboard API is localhost-only and is intended to be reached from `127.0.0.1` or `localhost` on the same machine.

Persistence rules:
- queued jobs survive a server restart
- running jobs are marked failed on restart with a recovery message
- retry creates a new job and, for API mode, a new run ID

This is intentionally a single-process local queue, not a distributed worker system.

## External Dependencies
- Leonardo API for production image generation
- Canva Connect API for asset upload, autofill, and export
- Local Chrome/Chromium plus Selenium for browser automation

## Supported vs Archived
- Supported: the Python CLI, Canva/Leonardo API clients in `dj_msqrvve_brand_system/src/`, and the dashboard
- Archived: legacy `canva/` and `leonardo/` scaffolds plus historical planning docs
