# Dashboard

Next.js control surface for local job queueing, monitoring, and gallery/history review.

## Local Development
```bash
npm install
npm run dev
```

Runs on `http://localhost:6767`.
The supported dev and start scripts bind to `127.0.0.1:6767`.

## Supported Checks
```bash
npm run lint
npm run test
npm run build
```

## Runtime Notes
- The dashboard shells out to `../dj_msqrvve_brand_system/src/main.py`.
- Job state is persisted to `../dj_msqrvve_brand_system/outputs/dashboard-jobs.json`.
- Browser automation jobs run headless and require an existing bootstrapped Firefox profile.
- The queue is intentionally single-worker and local-first.
- Supported execution uses the queue-backed `/api/jobs` routes only.
- Dashboard API routes reject non-localhost traffic.
