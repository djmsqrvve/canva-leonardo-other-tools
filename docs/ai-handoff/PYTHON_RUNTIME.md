# Python Runtime

## Entry Points
- `src/main.py` is the supported CLI.
- `src/auth_server.py` is the supported Canva OAuth bootstrap helper.
- `src/test_health.py` is the supported manual live-provider health and smoke-plan helper.
- `src/cli.py` is deprecated compatibility scaffold only.

## Supported CLI Commands
- `python src/main.py generate-api <asset_key>`
- `python src/main.py generate-browser "<prompt_or_prompt_key>"`

Do not rename these commands without an explicit migration decision.

## `generate-api` Flow
`generate-api` does the following:
1. Load `.env` and prompt config.
2. Resolve the Leonardo model and prompt payload.
3. Generate through the Leonardo API.
4. Download the raw output locally.
5. Optionally sync the raw asset into Canva.
6. Optionally autofill a Canva template.
7. Optionally export the Canva design.
8. Write stage-by-stage ledger entries to `outputs/ledger.jsonl`.

Key files:
- `src/main.py`
- `src/apis/leonardo_api.py`
- `src/apis/canva_api.py`
- `src/lib/pipeline.py`

## API Retry And Resume Model
- Each API run gets a run ID.
- A ledger idempotency key combines `run_id`, asset key, and prompt hash.
- Completed stages can be reused on retries when the same run ID is supplied.
- Failed runs now print the run ID, failed stage, ledger path, and output directories for faster live debugging.

## Canva Behavior
- Canva access tokens are read from `CANVA_ACCESS_TOKEN`.
- If `CANVA_REFRESH_TOKEN`, `CANVA_CLIENT_ID`, and `CANVA_CLIENT_SECRET` are present, Canva calls can refresh access tokens in-process and retry once on `401` or `403`.
- Refreshed values are written back to `.env` when that file exists.
- Autofill and export require a real template ID in `config/prompts.local.yaml`.
- Public `config/prompts.yaml` intentionally keeps placeholder `TEMPLATE_ID_HERE` values.

Relevant files:
- `src/apis/canva/auth.py`
- `src/apis/canva/base.py`
- `src/apis/canva_api.py`
- `src/auth_server.py`

## `generate-browser` Flow
- Uses Selenium against Leonardo web UI.
- Requires `requirements-browser.txt`.
- Requires local Chrome or Chromium, either on `PATH` or via `CHROME_BINARY`.
- Headless mode only works after the local `user_profile/` contains a valid interactive session.
- If the saved session expires, rerun `generate-browser` without `--headless` to refresh the profile.
- Browser failures write artifacts to `outputs/browser-artifacts/`.

Relevant file:
- `src/lib/leonardo_browser.py`

## Config Files
- `config/prompts.yaml`: public sample prompt and model config.
- `config/prompts.local.yaml`: local gitignored `canva_templates` override only.
- `.env`: local credential store used by the supported flows.

## Dependencies
- `requirements-runtime.txt`: runtime-only Python deps.
- `requirements-dev.txt`: supported local development/test baseline.
- `requirements-browser.txt`: optional browser automation deps.

## Tests
- `tests/test_main.py`: CLI workflow and ledger behavior.
- `tests/test_canva_client.py`: Canva auth, refresh, and job behavior.
- `tests/test_browser_preflight.py`: browser preflight and browser error handling.
- `tests/test_health_script.py`: manual smoke helper behavior.
- `tests/test_leonardo_client.py`: Leonardo API client behavior.
