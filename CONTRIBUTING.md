# Contributing Guide

## Setup
```bash
cd dj_msqrvve_brand_system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
cd ../dashboard
npm install
```

Install browser dependencies only if you are working on `generate-browser`:
```bash
cd ../dj_msqrvve_brand_system
pip install -r requirements-browser.txt
```

## Workflow
1. Start from a clean `main` branch.
2. Create a focused branch.
3. Make one coherent change at a time.
4. Run the supported validation commands.
5. Commit each validated change slice before moving to the next task or gap.
6. Open a PR with clear scope, risk, and rollback notes.

## Validation
Required for all code changes:
```bash
make health
```

Required for dashboard changes and recommended before every PR:
```bash
make full-check
```

## Commit Style
Use conventional-style subjects:

```text
type(scope): short summary
```

Examples:
- `fix(auth): validate canva oauth state`
- `docs(readme): split supported workflows from archived material`
- `test(dashboard): cover queue persistence after restart`

## Expectations
- Keep comments targeted and explain only non-obvious logic.
- Do not leave validated work uncommitted while continuing into the next development slice.
- Update docs when behavior or setup changes.
- Do not add new behavior to deprecated or archived surfaces.
- Keep public-facing examples aligned with real supported workflows.
