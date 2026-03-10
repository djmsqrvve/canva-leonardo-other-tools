# AI Handoff Suite

Read this folder before making changes to the repo.

Canonical repo: `/home/dj/dev/canva_leonardo_other_tools`
Branch at audit time: `main`
HEAD at audit time: `dbc6030`
Worktree at audit time: uncommitted handoff-suite changes only

Recommended order:
1. [Accuracy Audit](./00_ACCURACY_AUDIT.md)
2. [Current State](./CURRENT_STATE.md)
3. [Repo Map](./REPO_MAP.md)
4. [Python Runtime](./PYTHON_RUNTIME.md)
5. [Dashboard Runtime](./DASHBOARD_RUNTIME.md)
6. [Operations And Validation](./OPERATIONS_AND_VALIDATION.md)
7. [Live Smoke And Event Integration](./LIVE_SMOKE_AND_EVENT_INTEGRATION.md)
8. [Agent Guardrails](./AGENT_GUARDRAILS.md)
9. [Plan](./PLAN.md)
10. [Prompt](./PROMPT.md)
11. [Audit Request](./AUDIT_REQUEST.md)
12. [Session Handoff 2026-03-09](./SESSION_HANDOFF_2026-03-09.md) *(start here if resuming from Mar 9)*

This suite is the fast-path handoff for a new coding agent. It is intentionally limited to the maintained surfaces and the adjacent reference material that still matters during active work.

Primary truths:
- Supported runtime surfaces are `dj_msqrvve_brand_system/` and `dashboard/`.
- `docs/archive/` and `archive/` are historical reference only.
- The dashboard is localhost-only and queue-based.
- Public Canva template mappings stay as placeholders; real template IDs live in gitignored local overrides.
- Canva runtime calls can refresh tokens in-process when refresh credentials are configured.
- Leonardo browser automation depends on a locally bootstrapped Firefox profile and writes failure artifacts locally.
- The repo state described above belongs to `/home/dj/dev/canva_leonardo_other_tools`, not to the event workspace in `brand`.
- MSQRVVE Madness asset production depends on both this repo and `/home/dj/dev/brand/stream/events/msqrvve_madness_march_subathon_2026`.

If you only need one file, start with [Current State](./CURRENT_STATE.md).
