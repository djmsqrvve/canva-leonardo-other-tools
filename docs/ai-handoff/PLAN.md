# Implementation Plan — Architecture, API, and Testing Improvements

Updated: 2026-03-10

Full plan details: `~/.claude/plans/iridescent-honking-avalanche.md`

## Phases (execute in order)

### Phase 1: API Retry Logic + Atomic Ledger Writes
- Add `with_retries()` helper to `src/lib/utils.py`
- Integrate into LeonardoClient and CanvaBaseClient `_request()` methods
- Add `fsync` to ledger writes in `src/lib/pipeline.py`
- ~5 new tests

### Phase 2: Extract Business Logic from main.py
- Create `src/commands/` package (generate_api, generate_browser, generate_batch, suggest)
- Add `PipelineContext` dataclass to `src/lib/pipeline.py`
- Thin main.py from 717 lines to ~200 (CLI dispatcher only)
- Existing 68 tests must pass without modification

### Phase 3: Test Coverage Expansion (~20 new tests)
- Gallery Flask tests (`tests/test_gallery.py`)
- Batch generation tests
- Malformed API response tests
- Token refresh edge cases

### Phase 4: Download Hardening + Correlation IDs
- Min-size validation, Content-Length checks, streaming downloads
- Add `correlation_id` field linking Leonardo + Canva pipeline events

### Phase 5: Ledger Index + Configurable Timeouts
- `LedgerIndex` class for O(1) lookups
- Env-var-configurable timeouts for API clients

### Phase 6: Playwright Visual Smoke Tests
- E2E tests for gallery UI with `@pytest.mark.e2e`
- Screenshots to `outputs/screenshots/`

## Dependencies
```
Phase 1 → Phase 2 → Phase 4 (uses PipelineContext)
                   → Phase 5 (uses PipelineContext)
           Phase 3 (parallel with Phase 2)
                   → Phase 6 (uses gallery test patterns)
```
