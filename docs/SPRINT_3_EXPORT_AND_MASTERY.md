# Sprint Plan: Phase 3 - Asset Retrieval & Format Mastery
**Objective:** Close the loop by programmatically exporting finished Canva designs for use in OBS, Twitch, and Game Engines.

## 🛠 Tasks
### 3.1 Design Export Engine (`src/lib/canva_api.py`)
- Implement `export_design(design_id, format='png')` with format validation (PDF, JPG, MP4, etc.).
- Implement `poll_export_job(job_id)` with a download utility to pull assets into the correct local directory.
- Add `get_export_formats(design_id)` to list allowed formats per design.

### 3.2 Automation Post-Processing (`src/lib/image_processor.py`)
- Create a post-processor that takes the exported Canva file.
- Implement specialized routines (resize to power-of-two for Bevy, create 9-slice UI for Roblox).

### 3.3 Final "Down-to-the-Tee" CLI CLI Commands
- `dj download [design_id]`: Manual download of any Canva design in the account.
- `dj asset-master [id]`: A "magic" command that downloads, processes, and pushes a Canva asset into the project folders (`helix`, `bevy`, `obs`).

## ✅ Definition of Done
- A final PNG or MP4 asset is generated from a text prompt and lands in the target project folder without any manual Canva work.
- The pipeline is fully tested and verified with the existing test suite.
