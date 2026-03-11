# Current State

Updated: 2026-03-10

## Git Snapshot

- Canonical repo: `/home/dj/dev/canva_leonardo_other_tools`
- Branch: `main`
- Worktree: clean
- Tests: 68 Python (all passing), dashboard tests passing

## CLI Commands

All via `cd dj_msqrvve_brand_system && PYTHONPATH=src venv/bin/python -m main`:

| Command | Purpose |
|---------|---------|
| `generate-browser <key> --headless` | Single browser generation via Firefox |
| `generate-batch --category social --headless --sync` | Batch by category |
| `generate-batch --all --headless` | Generate all 13 asset types |
| `generate-batch <key> --variants 3 --headless` | Multiple variants |
| `generate-api <key> --sync --autofill --export png` | Full API pipeline |
| `canva-auth` | Check/refresh Canva token |
| `gallery --port 6868` | Launch asset gallery |
| `suggest` | Show what to generate next |

## Architecture

### Browser hierarchy
```
BrowserBase (src/lib/browser/driver.py)
├── LeonardoBrowser (src/lib/leonardo_browser.py)  — image generation
└── CanvaBrowser (src/apis/canva/browser.py)       — design editor automation
```

### API clients
- `LeonardoClient` (src/apis/leonardo_api.py) — API key auth, generation + polling
- `CanvaClient` (src/apis/canva_api.py) — facade over Assets, Autofill, Exports, Designs sub-clients
- `CanvaTokenManager` (src/apis/canva/auth.py) — OAuth token refresh + .env persistence

### Pipeline
- Ledger: `outputs/ledger.jsonl` — JSONL append-only, stage-level idempotency
- Outputs: `outputs/raw/<run_id>/`, `outputs/exports/<run_id>/`
- Gallery ratings: `outputs/ratings.json`
- Browser artifacts: `outputs/browser-artifacts/`

### Prompt categories
| Category | Canva Folder | Example prompts |
|----------|-------------|-----------------|
| social | DJ Brand/Social Banners | social_banner_bg, profile_avatar |
| stream_alerts | DJ Brand/Stream Alerts | raid_alert_art, follower_icon |
| madness | DJ Brand/MSQRVVE Madness | madness_launch_key_art + 5 more |
| game_2d | DJ Brand/Game Assets | helix2000_tileset_grass |
| game_3d | DJ Brand/Game Assets | helix_main_texture_metal, bevy_skybox |

## Environment

- Python: 3.13.12 via `dj_msqrvve_brand_system/venv/`
- Node: v25.7.0 via `~/.nvm/versions/node/v25.7.0/bin/`
- Firefox: `/usr/bin/firefox` (snap)
- Firefox profile: `~/snap/firefox/common/.mozilla/firefox/ebfog0e6.default`

## Known Limitations

- Leonardo API key not provisioned — `generate-api` blocked by design
- Browser selectors hardcoded; Leonardo UI changes break automation
- Ledger is O(n) scan per stage lookup (no indexing)
- No retry logic on Leonardo API client for transient failures
- Gallery has no auth or pagination
- Single-process local queue in dashboard (not distributed)
