# Resume — Next Session

## Where we left off

Session 2 (2026-03-10) is committed. All session work is on `main`, worktree is clean. 68 tests passing.

## What to do next

**Start with Phase 1** of the improvement plan.

### Phase 1a: Add `with_retries()` to `src/lib/utils.py`
```python
# Signature to implement:
def with_retries(
    fn: Callable[[], T],
    *,
    max_retries: int = 3,
    retryable: tuple[type[Exception], ...] = (RateLimitError,),
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 30.0,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> T:
```
- Reuse existing `compute_backoff_schedule()` for delays
- Support `Retry-After` header on `RateLimitError`
- `sleep_fn` param for instant tests (matches `poll_job` pattern)

### Phase 1b: Integrate into API clients
- `src/apis/leonardo_api.py` — wrap `requests.request()` in `_request()` line 29
- `src/apis/canva/base.py` — wrap inner HTTP call; leave existing 401 refresh-and-retry untouched

### Phase 1c: Harden ledger writes
- `src/lib/pipeline.py` line 89 — add `file_obj.flush(); os.fsync(file_obj.fileno())`

### Tests to write
- `tests/test_utils.py`: retries succeed after transient, exhaust max, skip non-retryable
- `tests/test_pipeline.py`: ledger skips truncated lines, fsync on append

### Verify
```bash
cd dj_msqrvve_brand_system && venv/bin/python -m pytest --tb=short
```

## Key files to read first
1. `src/lib/utils.py` — where `with_retries()` goes (111 lines)
2. `src/apis/leonardo_api.py` — zero retry logic today (95 lines)
3. `src/lib/pipeline.py` — ledger append at line 86 (118 lines)
4. `src/lib/errors.py` — `RateLimitError` and exception hierarchy

## Full plan reference
`~/.claude/plans/iridescent-honking-avalanche.md`
