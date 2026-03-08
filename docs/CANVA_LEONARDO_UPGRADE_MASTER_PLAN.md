# Canva + Leonardo Tools Upgrade Master Plan

## Scope

This plan upgrades the full `canva_leonardo_other_tools` stack:

1. `dj_msqrvve_brand_system` (Python CLI + API clients)
2. `dashboard` (Next.js control surface)
3. `stream_ops` integration surfaces
4. Test, release, and operational docs

## Current Gaps (March 8, 2026)

1. `AssetsClient.upload_asset()` is still a placeholder (`pass`) in `src/apis/canva/assets.py`.
2. No shared polling/retry utility for async Canva/Leonardo jobs.
3. `src/main.py` supports generation but not end-to-end sync/autofill/export orchestration.
4. `src/cli.py` is scaffold/mocked and not aligned with production command surface.
5. Dashboard API route shells out using interpolated strings and has no job queue/status model.
6. Limited test coverage for production paths (upload, autofill polling, export download).
7. No central artifact ledger for traceability from prompt -> asset -> Canva design -> export file.

## Target End State

1. One reliable command path from prompt to final exported asset.
2. Repeatable folder strategy in Canva and local filesystem.
3. Deterministic job tracking, retries, and failure reporting.
4. Dashboard with async job status, history, and retry controls.
5. Production-grade security and QA gates.

## Timeline (Proposed)

1. Phase 0: March 8-9, 2026
2. Phase 1: March 9-11, 2026
3. Phase 2: March 11-13, 2026
4. Phase 3: March 13-15, 2026
5. Phase 4: March 15-18, 2026
6. Phase 5: March 18-20, 2026
7. Phase 6: March 20-21, 2026

## Phase 0: Baseline and Freeze

### Objective
Lock baseline behavior and create upgrade-safe guardrails.

### Tasks
1. Capture baseline commands and outputs for `generate-browser` and `generate-api`.
2. Create a capability matrix doc (supported vs placeholder features).
3. Define canonical command interface for CLI v2.
4. Add a `make health` or equivalent script for quick environment validation.

### Deliverables
1. Baseline report in `docs/`.
2. Finalized CLI command contract.

### Exit Criteria
1. Team agrees on command surface and feature priorities.

## Phase 1: Core API Hardening (P0)

### Objective
Make Canva + Leonardo API clients production-usable.

### Tasks
1. Implement real Canva asset upload in `src/apis/canva/assets.py`.
2. Add `src/lib/utils.py` with shared polling, retry/backoff, timeout helpers.
3. Implement folder auto-discovery and create-if-missing behavior.
4. Add explicit typed exceptions for auth, rate limit, timeout, and API failure states.
5. Normalize response parsing so all clients return consistent result objects.

### Deliverables
1. Working upload + folder path flow.
2. Shared job polling utility used by Canva and Leonardo clients.

### Exit Criteria
1. Single command can upload an existing local file to a target Canva folder.
2. Polling utility handles success, timeout, and failure states with clear logs.

## Phase 2: Pipeline Orchestrator and Asset Sync (P0)

### Objective
Chain generation -> sync -> optional autofill in one reliable flow.

### Tasks
1. Extend `src/main.py` with flags:
- `--sync`
- `--autofill`
- `--export`
2. Add local artifact ledger (JSONL preferred) with run IDs and timestamps.
3. Add deterministic output directories:
- `outputs/raw/`
- `outputs/canva/`
- `outputs/exports/`
4. Add idempotency key strategy to avoid duplicate job creation.

### Deliverables
1. Orchestrated pipeline path from generation to Canva sync.
2. Run ledger with searchable entries.

### Exit Criteria
1. `generate-api <asset_key> --sync` stores metadata and uploads output to Canva automatically.

## Phase 3: Template Autofill + Export Mastery (P1)

### Objective
Automate design composition and export retrieval end-to-end.

### Tasks
1. Expand template mappings in `config/prompts.yaml` with data fields schema.
2. Add autofill polling + design link retrieval.
3. Add export polling + file download with format validation.
4. Add post-export processors for stream/platform targets.

### Deliverables
1. Template autofill job chain with robust status handling.
2. Local export downloader with organized destination paths.

### Exit Criteria
1. One command produces final Canva design and downloaded export file.

## Phase 4: Dashboard v2 (Queue, Status, History) (P1)

### Objective
Upgrade dashboard from direct command trigger to reliable async control plane.

### Tasks
1. Replace shell-string execution in `dashboard/src/app/api/generate/route.ts` with argument-safe process spawning.
2. Add job queue model (queued/running/success/failed/canceled).
3. Add status endpoint + polling UI.
4. Add history view backed by ledger data.
5. Add retry/cancel controls for failed/stuck jobs.

### Deliverables
1. Stable dashboard workflow for long-running generations.
2. Accurate per-job logs and status surfaces.

### Exit Criteria
1. Dashboard can safely execute and monitor multiple concurrent jobs.

## Phase 5: QA, Security, and Reliability (P0/P1)

### Objective
Make the upgraded stack safe to operate repeatedly in production.

### Tasks
1. Expand tests:
- API client unit tests
- orchestration integration tests
- dashboard API route tests
2. Add schema validation for prompt config and runtime payloads.
3. Add secrets handling rules and redact sensitive values in logs.
4. Add structured logging with run IDs across CLI and dashboard.
5. Add failure injection tests (timeouts, 429, invalid tokens).

### Deliverables
1. CI-quality test matrix and pass criteria.
2. Security + logging standards doc.

### Exit Criteria
1. Test suite validates core happy path + top failure paths.
2. No secrets printed in standard logs.

## Phase 6: Release and Handoff

### Objective
Cut over to upgraded tooling with clean docs and operational runbooks.

### Tasks
1. Publish migration notes for old commands.
2. Update all docs with new command examples.
3. Run final smoke tests:
- API-only flow
- browser-only flow
- mixed flow
- dashboard-triggered flow
4. Write rollback instructions.

### Deliverables
1. Release checklist and signoff artifact.
2. New-agent handoff doc with startup sequence.

### Exit Criteria
1. New agent can run full pipeline in under 30 minutes from docs only.

## Priority Backlog

### P0 (Do First)
1. Real Canva upload implementation.
2. Shared polling utility.
3. `--sync` orchestration.
4. Secure dashboard process execution.
5. Ledger + run ID tracing.

### P1 (Do Next)
1. Autofill data-field automation.
2. Export polling + downloader.
3. Queue-based dashboard job control.
4. Structured post-processing outputs.

### P2 (Optimization)
1. UI progress bars + richer UX.
2. Batch presets and profile switching.
3. Cost/performance dashboards.

## Engineering Standards for Upgrades

1. Every new command must have at least one unit test.
2. Every API call path must include timeout + retry strategy.
3. All file writes must be deterministic and namespaced by run ID.
4. All long-running jobs must emit structured status updates.

## Definition of Success

1. Prompt-to-export flow is one command for core asset types.
2. Dashboard operations are asynchronous, observable, and safe.
3. Agent handoff requires no tribal knowledge.
4. Failures are diagnosable from logs and ledger entries.
