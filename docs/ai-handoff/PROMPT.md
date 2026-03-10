# Next-Agent Prompt

You are taking over the Canva automation repo for MSQRVVE Madness. Use the
current local repo truth and keep the event workspace boundary explicit.

Read these files first:

1. `/home/dj/dev/canva_leonardo_other_tools/docs/ai-handoff/00_ACCURACY_AUDIT.md`
2. `/home/dj/dev/canva_leonardo_other_tools/docs/ai-handoff/CURRENT_STATE.md`
3. `/home/dj/dev/canva_leonardo_other_tools/docs/ai-handoff/OPERATIONS_AND_VALIDATION.md`
4. `/home/dj/dev/canva_leonardo_other_tools/docs/ai-handoff/LIVE_SMOKE_AND_EVENT_INTEGRATION.md`
5. `/home/dj/dev/brand/stream/events/msqrvve_madness_march_subathon_2026/handoff/HANDOFF_PROJECT_CANVA_ASSET_PRODUCTION.md`

Ground truth:

- repo: `/home/dj/dev/canva_leonardo_other_tools`
- branch: `main`
- HEAD: `dbc6030`
- worktree: clean
- handoff suite path: `/home/dj/dev/canva_leonardo_other_tools/docs/ai-handoff`

Critical rules:

- real Canva template IDs must stay out of git
- public `config/prompts.yaml` remains placeholder-safe
- event readiness is split across this repo and the event workspace in `brand`

Your first response should restate the actual repo boundary, identify the next
safe live-smoke step, and list any event-side blockers that still prevent
declaring the Canva lane ready.
