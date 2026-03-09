# Agent Guardrails

## Stable Contracts
- Keep CLI command names stable: `generate-api`, `generate-browser`.
- Keep dashboard job statuses stable: `queued`, `running`, `success`, `failed`, `canceled`.
- Keep the dashboard local-first and single-process unless explicitly told otherwise.
- Keep supported dashboard execution queue-based through `/api/jobs`.
- Keep the dashboard localhost-only unless there is an explicit product decision to widen that boundary.

## Do Not Regress
- Do not bring archived code or docs back into the supported surface by accident.
- Do not promise Canva autofill/export workflows from public sample config alone.
- Do not assume browser automation works without a bootstrapped `user_profile/`.
- Do not remove Canva refresh behavior or `.env` persistence without replacing it with an explicit supported alternative.

## Editing Rules That Matter In Practice
- Treat a dirty worktree as intentional unless you verify a concrete bug and fix it deliberately.
- Commit each validated work slice before moving to the next task.
- Update docs when setup, behavior, or operational recovery changes.
- Keep comments sparse and targeted.
- Prefer reading the active surfaces first instead of exploring archived scaffolds.

## When Extending Features
- Python runtime changes usually need updates in:
  `src/main.py`, supporting clients/helpers, tests, and operator docs.
- Dashboard changes usually need updates in:
  API handlers, runtime/state logic, tests, and dashboard-facing docs.
- Browser flow changes should consider:
  preflight behavior, session expiry handling, artifacts, and smoke guidance.
- Canva changes should consider:
  token lifecycle, private template config, and public-doc safety.

## Where To Look For Ground Truth
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/OPERATIONS.md`
- `dj_msqrvve_brand_system/DOCS.md`
- `docs/ai-handoff/`

If those conflict with older archived material, prefer the maintained docs and current code.
