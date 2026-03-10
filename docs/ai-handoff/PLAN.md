# Implementation Plan

## Immediate Priorities

1. Keep the repo truthful about public-vs-private Canva configuration.
2. Use manual live smoke before claiming runtime readiness.
3. Coordinate with the event workspace when template IDs or staged assets
   change.

## Safe Next Work

- bootstrap Leonardo browser profile if `user_profile/` is not seeded
- run headless browser smoke against a non-event prompt key
- run Canva smoke (sync, then autofill/export after template IDs exist)
- map real template IDs in `config/prompts.local.yaml`
- stage generated assets to event workspace
- dashboard job-runtime hardening
- (deferred) provision `LEONARDO_API_KEY` to unlock `generate-api` path

## Avoid By Default

- committing tenant secrets
- treating placeholder template IDs as ready
- assuming the event workspace and Canva repo are the same repo
