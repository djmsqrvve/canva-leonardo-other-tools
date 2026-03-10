# Implementation Plan

## Immediate Priorities

1. Keep the repo truthful about public-vs-private Canva configuration.
2. Use manual live smoke before claiming runtime readiness.
3. Coordinate with the event workspace when template IDs or staged assets
   change.

## Safe Next Work

- real local smoke against valid Canva credentials
- template-ID mapping via gitignored local overrides
- asset-export and event staging improvements
- dashboard job-runtime hardening

## Avoid By Default

- committing tenant secrets
- treating placeholder template IDs as ready
- assuming the event workspace and Canva repo are the same repo
