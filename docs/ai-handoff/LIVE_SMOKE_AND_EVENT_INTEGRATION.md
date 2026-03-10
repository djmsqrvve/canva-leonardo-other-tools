# Live Smoke And Event Integration

## Repo Boundary

This repo owns:

- Canva OAuth bootstrap and refresh flow
- Leonardo API and browser generation runtime
- local dashboard job execution
- local runtime state and failure artifacts

This repo does not own:

- event blocker truth
- event launch gating
- staged-event asset acceptance
- OBS mutation policy

Those live in:

- `/home/dj/dev/brand/stream/events/msqrvve_madness_march_subathon_2026`

## High-Value Event Touchpoints

- `handoff/HANDOFF_PROJECT_CANVA_ASSET_PRODUCTION.md`
- `operations/CANVA_TEMPLATE_API_403_2026-03-08.md`
- `operations/CANVA_TEMPLATE_ID_REGISTRY_DAY02.md`
- `operations/CANVA_LEONARDO_OBS_ASSET_HANDOFF.md`

## Real Template ID Policy

- Public `config/prompts.yaml` stays placeholder-safe.
- Real `canva_templates` mappings belong in
  `dj_msqrvve_brand_system/config/prompts.local.yaml`.
- Do not claim readiness while required event keys still resolve to
  `TEMPLATE_ID_HERE`.

## Suggested Smoke Sequence

1. `cd /home/dj/dev/canva_leonardo_other_tools/dj_msqrvve_brand_system`
2. `./venv/bin/python src/test_health.py auth`
   — Leonardo will show `[BLOCKED]` (expected, no API key). Canva `[OK]` is the signal that matters.
3. Bootstrap browser profile if not seeded: run `generate-browser` interactively
   (without `--headless`) to log in and save `user_profile/`.
4. `./venv/bin/python src/main.py generate-browser "<prompt>"` with `--headless`
   to verify headless generation works.
5. Verify event-side blocker state in the `brand` workspace before treating the
   Canva lane as launch-ready.

## Acceptance For MSQRVVE Event Work

- Canva auth and refresh path work locally.
- Required event template mappings exist in local overrides.
- Generated assets are staged to the event/Streamtools destination expected by
  the event handoff.
- The event blocker register reflects the current truth after smoke or rollout.
