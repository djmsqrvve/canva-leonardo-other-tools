# Canva + Leonardo Upgrade Agent Handoff Guide

Use this guide when assigning a new agent to the upgrade plan.

## Required Reading Order

1. `docs/archive/CANVA_LEONARDO_UPGRADE_MASTER_PLAN.md`
2. `docs/archive/TODO_NEXT_2026-03-09.md`
3. `docs/archive/SPRINT_1_ASSET_SYNC.md`
4. `docs/archive/SPRINT_2_AUTOFILL_PIPELINE.md`
5. `docs/archive/SPRINT_3_EXPORT_AND_MASTERY.md`
6. `dj_msqrvve_brand_system/DOCS.md`

## Day 1 Startup Checklist

1. Validate Python environment:
```bash
cd /home/dj/dev/canva_leonardo_other_tools/dj_msqrvve_brand_system
source venv/bin/activate
python3 src/main.py --help
```
2. Validate dashboard:
```bash
cd /home/dj/dev/canva_leonardo_other_tools/dashboard
npm run dev
```
3. Validate tests:
```bash
cd /home/dj/dev/canva_leonardo_other_tools
make test
```

## Immediate Implementation Order (P0)

1. Implement `upload_asset()` in `src/apis/canva/assets.py`.
2. Add shared polling utility in `src/lib/utils.py`.
3. Wire `--sync` path in `src/main.py`.
4. Add ledger writer and run ID propagation.
5. Harden dashboard route process execution.

## Code Ownership Map

1. CLI orchestration:
- `dj_msqrvve_brand_system/src/main.py`
2. API clients:
- `dj_msqrvve_brand_system/src/apis/canva/*.py`
- `dj_msqrvve_brand_system/src/apis/leonardo_api.py`
3. Dashboard API + UI:
- `dashboard/src/app/api/generate/route.ts`
- `dashboard/src/app/page.tsx`
4. Tests:
- `dj_msqrvve_brand_system/tests/*`

## Completion Criteria Per Shift

1. All changed commands are documented with example usage.
2. Tests added/updated for changed behavior.
3. Any breaking command change listed in shift notes.
4. Next agent has exact next step and command.

## Shift Handoff Template

Copy this into a dated note each shift.

### Metadata
- Date:
- Agent:
- Phase:

### Completed
1.
2.
3.

### Files Changed
1.
2.

### Commands Executed
```bash
# paste exact commands
```

### Test Evidence
```bash
# paste test command + result summary
```

### Blockers
1.
2.

### Next Agent First Command
```bash
# one exact command to continue
```
