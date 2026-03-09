# Dashboard Runtime

## Purpose
`dashboard/` is the local control plane for queueing jobs, tracking status, and reading ledger-backed run history.

## Runtime Model
- Next.js app running on `127.0.0.1:6767`.
- Queue execution is local-first and single-process.
- Jobs shell out to the Python CLI in `../dj_msqrvve_brand_system/src/main.py`.
- Queue state persists to `../dj_msqrvve_brand_system/outputs/dashboard-jobs.json`.
- API history is read from `../dj_msqrvve_brand_system/outputs/ledger.jsonl`.

## Supported API Surface
- `/api/jobs`
- `/api/jobs/[jobId]`
- `/api/jobs/[jobId]/cancel`
- `/api/jobs/[jobId]/retry`
- `/api/jobs/history`

The legacy direct execution route is not part of the supported surface.

## Security Boundary
- The dashboard is intentionally localhost-only.
- Route handlers reject non-loopback host, origin, or forwarded-client traffic.
- The dev and start scripts bind to `127.0.0.1`.
- There is no supported remote multi-user mode.

## Stable Job Model
Stable statuses:
- `queued`
- `running`
- `success`
- `failed`
- `canceled`

Behavior:
- Queued jobs survive restart.
- Jobs that were `running` during restart are marked `failed`.
- Retrying a failed job creates a new job.
- API-mode retries also get a new run ID.

## File Guide
- `src/app/page.tsx`: dashboard page and client interactions.
- `src/app/api/jobs/route.ts`: route wiring.
- `src/lib/job-runtime.js`: queue scheduler, process lifecycle, persistence, recovery.
- `src/lib/jobs-api-handler.js`: request validation and runtime coordination.
- `src/lib/generation-command.js`: command assembly for API or browser mode.
- `src/lib/generation-helpers.js`: shared payload validation and stdout URL extraction.
- `src/lib/ledger-history.js`: aggregates stage events from the Python ledger.
- `src/lib/localhost-request.js`: loopback request evaluation and 403 handling.

## Browser Jobs
- Browser jobs run headless from the dashboard.
- They require an already bootstrapped `dj_msqrvve_brand_system/user_profile/`.
- Browser jobs do not currently write ledger history.
- Failures should be investigated through dashboard job output plus Python-side browser artifacts.

## Validation
- `npm run lint`
- `npm run test`
- `npm run build`

Repo-level validation uses `make full-check`.
