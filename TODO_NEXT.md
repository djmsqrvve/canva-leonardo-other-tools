# TODO NEXT: Merge Stabilization + Post-Merge Targets (March 9, 2026)

Target: Merge `feature/p0-core-pipeline` safely, then start Phase 4 dashboard control-plane work.

## Completed in P0 (Implemented on feature branch)
- [x] Real Canva asset upload flow in `src/apis/canva/assets.py`.
- [x] Shared polling/backoff helpers in `src/lib/utils.py`.
- [x] Orchestrated `generate-api` contract in `src/main.py` (`--sync`, `--autofill`, `--export`, `--canva-folder`, `--run-id`).
- [x] Ledger + idempotency helpers in `src/lib/pipeline.py`.
- [x] Typed API errors in `src/lib/errors.py`.
- [x] Dashboard generate route switched from shell command strings to `spawn`.

## Active Priorities (Pre-Merge Stabilization)
- [ ] Ensure dashboard lint/test/build checks are green with route and UI tests.
- [ ] Close failure-path test gaps for generation/sync/autofill/export ledger behavior.
- [ ] Close API error-shape tests (auth/rate-limit/timeout/request failures).
- [ ] Confirm idempotent resume behavior and export re-download behavior in tests.
- [ ] Keep docs and PR checklist aligned with actual commands.

## Next Feature Targets (Post-Merge)
- [ ] Dashboard job queue model (`queued/running/success/failed/canceled`).
- [ ] Status endpoint + polling UI + history view sourced from ledger.
- [ ] Retry/cancel controls for failed or stalled jobs.
- [ ] Route parity for full CLI flags once queue/status flow is in place.

## Verification Commands
```bash
make health
cd dashboard && npm run lint
cd dashboard && npm run test
```
