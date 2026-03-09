# AI Handoff Suite

Read this folder before making changes to the repo.

Recommended order:
1. [Current State](./CURRENT_STATE.md)
2. [Repo Map](./REPO_MAP.md)
3. [Python Runtime](./PYTHON_RUNTIME.md)
4. [Dashboard Runtime](./DASHBOARD_RUNTIME.md)
5. [Operations And Validation](./OPERATIONS_AND_VALIDATION.md)
6. [Agent Guardrails](./AGENT_GUARDRAILS.md)

This suite is the fast-path handoff for a new coding agent. It is intentionally limited to the maintained surfaces and the adjacent reference material that still matters during active work.

Primary truths:
- Supported runtime surfaces are `dj_msqrvve_brand_system/` and `dashboard/`.
- `docs/archive/` and `archive/` are historical reference only.
- The dashboard is localhost-only and queue-based.
- Public Canva template mappings stay as placeholders; real template IDs live in gitignored local overrides.
- Canva runtime calls can refresh tokens in-process when refresh credentials are configured.
- Leonardo browser automation depends on a locally bootstrapped Chrome profile and writes failure artifacts locally.

If you only need one file, start with [Current State](./CURRENT_STATE.md).
