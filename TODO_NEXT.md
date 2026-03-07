# 📝 TODO: CLI Upgrades & Sprint 1 Execution (March 7, 2026)

Target: Finalize the "Shadowpunk Vault" and solidify the "Down-to-the-Tee" CLI.

## 🛠️ High-Priority CLI Upgrades
- [ ] **Real Asset Upload Logic:** Complete the `AssetsClient.upload_asset()` implementation in `src/apis/canva/assets.py` using the 2-step multipart upload flow.
- [ ] **Polling Utility:** Create a reusable `poll_job(job_id, api_type)` helper in `src/lib/utils.py` to handle asynchronous Canva/Leonardo tasks uniformly.
- [ ] **The `--sync` Flag:** Update `main.py` so that `generate-api --sync` automatically triggers the Leonardo -> Local -> Canva Upload pipeline.
- [ ] **Folder Auto-Discovery:** Implement `get_or_create_shadowpunk_folder()` to ensure assets land in `Shadowpunk/Generations` by default.

## 🎨 Aesthetic & UX Refinement
- [ ] **CLI Progress Bars:** Add `tqdm` or a custom "Bioluminescent Pulse" progress bar for long generation/upload tasks.
- [ ] **JSON Data Logging:** Implement a local `ledger.json` to track every generation (Prompt, URL, Canva Design ID) for easier debugging and retrieval.

## 🧪 Verification
- [ ] **End-to-End Test:** Successfully run `dj generate-api helix_tileset --sync` and verify the image appears in the Canva "Shadowpunk" folder.
- [ ] **Dashboard Sync:** Ensure the Next.js Dashboard gallery refreshes automatically when a new asset is synced to the vault.

---
**Current Port:** Dashboard running on http://localhost:6767
**Active Branch:** master (all changes committed)
