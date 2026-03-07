# Sprint Plan: Phase 1 - Asset Core & Organizational Sync
**Objective:** Solidify the "Shadowpunk Vault" by automating the transfer of Leonardo generations into a structured Canva library.

## 🛠 Tasks
### 1.1 Robust Asset Library (`src/lib/canva_api.py`)
- Implement `upload_asset(file_path, folder_id)` with polling for completion.
- Implement `get_or_create_folder(folder_name, parent_id='root')` to ensure organized storage.
- Add `list_assets(folder_id)` to verify uploads.

### 1.2 Asset Sync Script (`src/sync_assets.py`)
- Create a script that watches `game_assets/` or `assets/social_media/` folders.
- Automatically uploads new local files to the corresponding Canva folder.

### 1.3 CLI Integration
- Add `dj generate-api --sync` flag to automatically push Leonardo results to Canva.

## ✅ Definition of Done
- A local file can be uploaded to a specific Canva folder via a single CLI command.
- The `user_profile` in the browser route correctly sees these new assets in the "Projects" tab.
