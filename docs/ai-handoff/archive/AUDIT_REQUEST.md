# External Audit Request

You are the final external auditing AI for the Canva automation repo. Decide
whether this handoff suite is adequate for a new agent and final IDE closeout.

Read these files first:

1. `/home/dj/dev/canva_leonardo_other_tools/docs/ai-handoff/README.md`
2. `/home/dj/dev/canva_leonardo_other_tools/docs/ai-handoff/00_ACCURACY_AUDIT.md`
3. `/home/dj/dev/canva_leonardo_other_tools/docs/ai-handoff/CURRENT_STATE.md`
4. `/home/dj/dev/canva_leonardo_other_tools/docs/ai-handoff/OPERATIONS_AND_VALIDATION.md`
5. `/home/dj/dev/canva_leonardo_other_tools/docs/ai-handoff/LIVE_SMOKE_AND_EVENT_INTEGRATION.md`
6. `/home/dj/dev/brand/stream/events/msqrvve_madness_march_subathon_2026/handoff/HANDOFF_PROJECT_CANVA_ASSET_PRODUCTION.md`

Current repo truth to audit against:

- repo: `/home/dj/dev/canva_leonardo_other_tools`
- branch: `main`
- HEAD: `dbc6030`
- repo state: clean
- handoff suite path: `/home/dj/dev/canva_leonardo_other_tools/docs/ai-handoff`

Critical audit requirement:

- verify that the suite keeps the Canva repo boundary distinct from the event
  workspace in `brand`

Audit tasks:

1. Decide whether the suite is adequate for a new agent to continue Canva auth,
   smoke, and asset-production work.
2. Confirm whether private-vs-public template-ID handling is documented well
   enough.
3. Identify any missing live-smoke steps, event integration details, or repo
   boundary clarifications.
4. If not ready, provide exact markdown edits.

Required output:

- verdict: `ready` or `not ready`
- confidence: `high`, `medium`, or `low`
- missing or weak areas
- exact suggested doc edits if needed
