# Repo Map

## Top Level
- `README.md`: public-facing overview and supported workflows.
- `Makefile`: supported validation entrypoints.
- `CONTRIBUTING.md`: contribution and commit rules.
- `docs/`: maintained docs plus archived historical docs.
- `dj_msqrvve_brand_system/`: maintained Python runtime.
- `dashboard/`: maintained Next.js dashboard.
- `archive/`: archived scaffold code.

## Maintained Python Surface
- `dj_msqrvve_brand_system/src/main.py`: supported CLI entrypoint.
- `dj_msqrvve_brand_system/src/auth_server.py`: local Canva OAuth bootstrap helper.
- `dj_msqrvve_brand_system/src/test_health.py`: manual live-provider auth and smoke-plan helper.
- `dj_msqrvve_brand_system/src/apis/leonardo_api.py`: Leonardo production API client.
- `dj_msqrvve_brand_system/src/apis/canva_api.py`: Canva facade used by the CLI.
- `dj_msqrvve_brand_system/src/apis/canva/`: Canva token manager and subclients.
- `dj_msqrvve_brand_system/src/lib/leonardo_browser.py`: Leonardo browser automation.
- `dj_msqrvve_brand_system/src/lib/pipeline.py`: run IDs, output paths, ledger helpers.
- `dj_msqrvve_brand_system/src/lib/utils.py`: polling and download helpers.
- `dj_msqrvve_brand_system/tests/`: maintained Python tests.

## Maintained Dashboard Surface
- `dashboard/src/app/page.tsx`: main dashboard UI.
- `dashboard/src/app/api/jobs/route.ts`: queue-backed API route surface.
- `dashboard/src/lib/job-runtime.js`: in-memory queue plus disk-backed persistence/recovery.
- `dashboard/src/lib/jobs-api-handler.js`: route handler logic for queue operations.
- `dashboard/src/lib/generation-command.js`: Python CLI command construction.
- `dashboard/src/lib/generation-helpers.js`: shared payload validation/output parsing.
- `dashboard/src/lib/ledger-history.js`: read-only history aggregation from the Python ledger.
- `dashboard/src/lib/localhost-request.js`: loopback-only request guard.
- `dashboard/tests/`: maintained dashboard tests.

## Config And Local State
- `dj_msqrvve_brand_system/.env.example`: supported environment template.
- `dj_msqrvve_brand_system/config/prompts.yaml`: public sample prompt config.
- `dj_msqrvve_brand_system/config/prompts.local.example.yaml`: sample private Canva template override file.
- `dj_msqrvve_brand_system/config/prompts.local.yaml`: gitignored private local override file used at runtime.
- `dj_msqrvve_brand_system/user_profile/`: Chrome profile used by browser automation.
- `dj_msqrvve_brand_system/outputs/ledger.jsonl`: API ledger.
- `dj_msqrvve_brand_system/outputs/dashboard-jobs.json`: dashboard queue persistence.
- `dj_msqrvve_brand_system/outputs/browser-artifacts/`: browser failure screenshots, HTML dumps, and metadata.

## Adjacent Reference Material
- `assets/`, `game_assets/`, `shared/`, `bevy_project/`, `stream_ops/`, `pipeline_scripts/`: project-adjacent content and reference material. These are not primary runtime surfaces.
- `archive/README.md`: explains archived code.
- `docs/archive/README.md`: explains archived docs.

## Files A New Agent Usually Reads First
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/OPERATIONS.md`
- `dj_msqrvve_brand_system/DOCS.md`
- `dj_msqrvve_brand_system/src/main.py`
- `dj_msqrvve_brand_system/src/auth_server.py`
- `dj_msqrvve_brand_system/src/lib/leonardo_browser.py`
- `dashboard/src/lib/job-runtime.js`
- `dashboard/src/lib/generation-command.js`
