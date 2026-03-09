# Contributing Guide

## Workflow

1. Start from a clean `main` and create a focused branch:
```bash
git checkout main
git pull --ff-only origin main
git checkout -b feature/<short-scope>
```
2. Make focused changes and verify locally:
```bash
make health
```
3. Commit in small units with clear intent.
4. Push the branch and open a PR using `.github/pull_request_template.md`.
5. Merge to `main` only after test evidence is documented.

## Commit Message Standard

Use conventional-style commits:

```text
type(scope): short summary

Optional body with why/impact.
```

Common `type` values:
- `feat`: new behavior
- `fix`: bug fix
- `refactor`: code change without behavior change
- `test`: test additions/updates
- `docs`: documentation only
- `chore`: maintenance/tooling

Examples:
- `feat(canva): add asset upload job polling`
- `fix(cli): handle missing prompt keys with explicit error`
- `docs(setup): align README commands with main.py interface`

## History Rules

- Keep one concern per commit.
- Do not mix unrelated docs/code/test changes.
- Include a body when behavior changes, noting risk and validation.
- Never force-push `main`.
- Prefer `git pull --ff-only` to avoid accidental merge commits.

## Validation Checklist

Before pushing:

```bash
make health
```

For UI/API changes in dashboard:

```bash
make full-check
```
