# Current State

This handoff reflects repo state as of March 9, 2026.

## Git Snapshot

- Canonical repo: `/home/dj/dev/canva_leonardo_other_tools`
- Branch: `main`
- HEAD: `dbc6030`
- Worktree: clean
- Handoff suite path: `docs/ai-handoff/`
- Validation targets confirmed in `Makefile`: `health`, `full-check`

## Supported Runtime Surface
- `dj_msqrvve_brand_system/` is the maintained Python automation engine.
- `dashboard/` is the maintained local control plane.
- `docs/ARCHITECTURE.md`, `docs/OPERATIONS.md`, and `dj_msqrvve_brand_system/DOCS.md` are the maintained core docs.

## Historical Material
- `docs/archive/` contains previous plans, research, and old handoffs.
- `archive/` contains scaffold or prototype code that is not part of the supported runtime.
- Do not revive archived surfaces unless the task explicitly says to do that.

## Current Runtime Guarantees
- Stable CLI command names: `generate-api` and `generate-browser`.
- Stable dashboard job states: `queued`, `running`, `success`, `failed`, `canceled`.
- Dashboard execution is queue-backed through `/api/jobs` and related job-control routes only.
- Dashboard API routes are localhost-only and the dev/start scripts bind to `127.0.0.1:6767`.
- Dashboard queue persistence is local-first and single-process, not distributed.
- Running jobs interrupted by dashboard restart are surfaced as failed and retryable.

## Hardening Work Already Completed
- Canva OAuth bootstrap validates generated `state`.
- Canva refresh tokens are persisted when returned and are consumed by runtime API clients.
- Canva requests retry once on `401` or `403` through the refresh flow when refresh credentials are available.
- Public `config/prompts.yaml` keeps placeholder Canva template mappings.
- Real Canva template IDs are expected in gitignored `config/prompts.local.yaml`.
- Leonardo browser automation fails fast when optional deps, Chrome, or a bootstrapped profile are missing.
- Leonardo browser generation now uses adaptive result detection instead of a fixed wait.
- Browser failures write local artifacts to `dj_msqrvve_brand_system/outputs/browser-artifacts/`.
- The repo now has a supported manual live-provider smoke helper at `dj_msqrvve_brand_system/src/test_health.py`.

## What A New Agent Should Assume
- The dirty worktree should be treated as intentional if you encounter one later.
- Public docs must stay honest about tenant-specific configuration requirements.
- The fastest way to understand current behavior is to read `src/main.py`, `src/auth_server.py`, `src/lib/leonardo_browser.py`, `dashboard/src/lib/job-runtime.js`, and `dashboard/src/lib/generation-command.js`.
- Repo-level hardening gaps from the March 2026 cleanup pass are closed. The next meaningful work is usually live smoke execution against real local credentials, feature work, or bug fixes.
- Leonardo generation uses `generate-browser` (Selenium) only. `LEONARDO_API_KEY` is not provisioned, so `generate-api` and the `test_health.py` Leonardo auth check are both blocked by design.
- MSQRVVE Madness event delivery is cross-repo:
  - Canva runtime and dashboard live here
  - event ops live in `/home/dj/dev/brand/stream/events/msqrvve_madness_march_subathon_2026`
