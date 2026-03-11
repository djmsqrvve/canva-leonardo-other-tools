# AI Handoff Suite

Read this folder before making changes to the repo.

Canonical repo: `/home/dj/dev/canva_leonardo_other_tools`
Branch: `main`

Start here:
1. [Current State](./CURRENT_STATE.md) — what the repo looks like right now
2. [Plan](./PLAN.md) — phased improvement roadmap (architecture, API, testing)
3. [Resume](./RESUME.md) — specific next-session pickup instructions

Reference (stable, not dated):
- [Repo Map](./REPO_MAP.md)
- [Python Runtime](./PYTHON_RUNTIME.md)
- [Dashboard Runtime](./DASHBOARD_RUNTIME.md)
- [Operations And Validation](./OPERATIONS_AND_VALIDATION.md)
- [Live Smoke And Event Integration](./LIVE_SMOKE_AND_EVENT_INTEGRATION.md)
- [Agent Guardrails](./AGENT_GUARDRAILS.md)

Historical (do not treat as current):
- `archive/` — dated session handoffs, one-time audit docs

Primary truths:
- Supported runtime surfaces are `dj_msqrvve_brand_system/` and `dashboard/`.
- `docs/archive/` and repo-root `archive/` are historical reference only.
- The dashboard is localhost-only and queue-based.
- Public Canva template mappings stay as placeholders; real template IDs live in gitignored local overrides.
- Leonardo browser automation depends on a locally bootstrapped Firefox profile.
- MSQRVVE Madness asset production depends on both this repo and `/home/dj/dev/brand/stream/events/msqrvve_madness_march_subathon_2026`.
