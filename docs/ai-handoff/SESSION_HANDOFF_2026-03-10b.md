# Session Handoff — 2026-03-10 (session 2)

## What happened this session

Built the full visual iteration pipeline on top of the cleanup from session 1.
Decomposed the monolithic `LeonardoBrowser` into a shared browser base, added
`CanvaBrowser`, wired ledger tracking into the browser path, added batch
generation, a local gallery UI, token refresh hardening, and a feedback loop.

## Current repo state

- Repo: `/home/dj/dev/canva_leonardo_other_tools`
- Branch: `main`
- Worktree: **dirty** (uncommitted — all changes listed below)
- Tests: 68 Python — all passing

## Changes made

### Browser decomposition
1. **Shared browser base** — new `lib/browser/` package:
   - `profile.py` — Firefox profile discovery, session file sync, lock cleanup
   - `artifacts.py` — failure screenshot/page-source capture
   - `driver.py` — `BrowserBase` class: Firefox lifecycle, profile setup,
     headless toggle, modal dismissal, auth detection, context manager support
2. **`LeonardoBrowser` refactored** — now extends `BrowserBase`, reduced from
   427 lines to ~130. Only Leonardo-specific logic remains.
3. **`CanvaBrowser` created** — `apis/canva/browser.py`, extends `BrowserBase`.
   Headless Canva editor automation: sidebar nav, template application, image
   upload/placement, text insertion. Smoke-tested headless — logs into Canva OK.

### CLI — 6 new commands
4. **`canva-auth`** — checks Canva token validity, attempts refresh on 401.
5. **`generate-batch`** — batch generation across categories or with variants.
   Reuses one browser instance across all prompts for efficiency.
   - `--category social` / `--all` / `social_banner_bg --variants 3`
6. **`gallery`** — launches a local Flask gallery at `:6868` with image grid,
   filtering by category/asset type, lightbox, star ratings, favorites, and
   side-by-side compare mode.
7. **`suggest`** — reads ratings + ledger, shows ungenerated prompts grouped by
   category, top-rated images, and exact CLI commands to run next.

### Pipeline improvements
8. **Ledger for browser path** — `run_generate_browser()` now writes to
   `outputs/ledger.jsonl` (generation, download_raw, sync stages).
9. **Per-prompt Canva folder routing** — each prompt in `prompts.yaml` has a
   `category` and `canva_folder` field. Sync uses the prompt's folder instead of
   the global default.
10. **Token refresh logging** — `CanvaTokenManager.refresh_access_token()` now
    prints when a refresh succeeds.

### Config
11. **`prompts.yaml`** — all 13 prompts now have `category` (social,
    stream_alerts, madness, game_2d, game_3d) and `canva_folder` (e.g.
    `DJ Brand/Social Banners`).

## Files created

```
dj_msqrvve_brand_system/src/lib/browser/__init__.py
dj_msqrvve_brand_system/src/lib/browser/profile.py
dj_msqrvve_brand_system/src/lib/browser/artifacts.py
dj_msqrvve_brand_system/src/lib/browser/driver.py
dj_msqrvve_brand_system/src/apis/canva/browser.py
dj_msqrvve_brand_system/src/gallery.py
dj_msqrvve_brand_system/src/gallery_ui/index.html
```

## Files modified

```
dj_msqrvve_brand_system/src/main.py              (6 new commands, ledger for browser, batch, gallery, suggest)
dj_msqrvve_brand_system/src/lib/leonardo_browser.py  (refactored to use BrowserBase)
dj_msqrvve_brand_system/src/apis/canva/auth.py    (refresh logging)
dj_msqrvve_brand_system/config/prompts.yaml        (category + canva_folder on all prompts)
dj_msqrvve_brand_system/tests/test_browser_preflight.py (updated for new API names)
dj_msqrvve_brand_system/tests/test_main.py         (updated error message assertions)
```

## Key architecture notes for next agent

### CLI commands (all via `PYTHONPATH=src venv/bin/python -m main`)

| Command | Purpose |
|---------|---------|
| `generate-browser <key> --headless` | Single browser generation |
| `generate-batch --category social --headless --sync` | Batch by category |
| `generate-batch --all --headless` | Generate all 13 asset types |
| `generate-batch <key> --variants 3 --headless` | Multiple variants |
| `generate-api <key> --sync --autofill --export png` | Full API pipeline |
| `canva-auth` | Check/refresh Canva token |
| `gallery --port 6868` | Launch asset gallery |
| `suggest` | Show what to generate next |

### Browser base hierarchy

```
BrowserBase (lib/browser/driver.py)
  ├── LeonardoBrowser (lib/leonardo_browser.py)  — generate images
  └── CanvaBrowser (apis/canva/browser.py)       — design editor automation
```

Shared: profile sync, Firefox lifecycle, modal dismissal, artifact capture.
Site-specific: login flow, selectors, page navigation.

### Gallery

- Server: `src/gallery.py` (Flask, reads ledger + scans `outputs/raw/`)
- Frontend: `src/gallery_ui/index.html` (single file, no build step)
- Ratings: `outputs/ratings.json` (star 1-5 + favorite boolean per image)
- Serves images from `outputs/raw/<run_id>/<filename>`

### Ledger

Both browser and API paths now write to `outputs/ledger.jsonl`.
Stages: generation, download_raw, sync, autofill, export.
Each event has: timestamp, run_id, asset_key, idempotency_key, stage, status.

### Prompt categories

| Category | Canva Folder | Prompts |
|----------|-------------|---------|
| social | DJ Brand/Social Banners | social_banner_bg, profile_avatar |
| stream_alerts | DJ Brand/Stream Alerts | raid_alert_art, follower_icon |
| madness | DJ Brand/MSQRVVE Madness | madness_launch_key_art + 5 more |
| game_2d | DJ Brand/Game Assets | helix2000_tileset_grass |
| game_3d | DJ Brand/Game Assets | helix_main_texture_metal, bevy_skybox |

## What the next agent should do

### Task: Visual smoke tests with Playwright screenshots

The user wants to see working PNG screenshots of all web UIs. Set up Playwright
and capture screenshots of:

1. **Next.js Dashboard** (`dashboard/` at `:6767`)
   - Main page with job queue
   - Job submission flow
   - Successful job gallery

2. **Asset Gallery** (`gallery` command at `:6868`)
   - Main grid view with images
   - Category filter applied
   - Lightbox open on an image
   - Compare mode with 2+ images selected
   - Rating/favorite interactions

3. **Canva Auth Server** (`auth_server.py` at `:5000`)
   - Landing page / auth redirect

### How to approach

- Install Playwright in the project venv or a separate test environment
- Write a `tests/test_screenshots.py` (or `tests/e2e/`) that:
  1. Starts each server as a subprocess
  2. Navigates Playwright to each page
  3. Takes full-page screenshots
  4. Saves PNGs to `outputs/screenshots/`
- The gallery needs at least one image in `outputs/raw/` to be useful — either
  generate one first via `generate-browser` or create a dummy test image
- Dashboard needs `npm run dev` in `dashboard/`

### Prerequisites

```bash
# Python deps
cd dj_msqrvve_brand_system
venv/bin/pip install playwright
venv/bin/python -m playwright install firefox

# Start servers (in separate terminals or background)
PYTHONPATH=src venv/bin/python -m main gallery --port 6868
cd ../dashboard && ~/.nvm/versions/node/v25.7.0/bin/npm run dev
```

## Environment

- Python: 3.13.12 via `dj_msqrvve_brand_system/venv/`
- Node: v25.7.0 via nvm at `~/.nvm/versions/node/v25.7.0/bin/`
- Firefox: available (`/usr/bin/firefox`, snap-based)
- Firefox profile: `~/snap/firefox/common/.mozilla/firefox/ebfog0e6.default`
- Session sync: automatic on browser init (copies cookies to `user_profile/`)
