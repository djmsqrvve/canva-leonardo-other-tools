# Sprint Plan: Phase 2 - Template Autofill & Mass Design
**Objective:** Automate the "Designer" role by programmatically injecting Leonardo images into Canva Brand Templates.

## 🛠 Tasks
### 2.1 Autofill Engine (`src/lib/canva_api.py`)
- Enhance `autofill_template(template_id, data)` to handle multiple datasets (text + images).
- Implement `poll_autofill_job(job_id)` with a wait loop to wait for design completion.
- Add `get_design_url(design_id)` to quickly retrieve the finished edit link.

### 2.2 Template Mapping (`config/prompts.yaml`)
- Define the `data_fields` for each prompt (e.g., `HEADING`, `SUBHEADING`, `BACKGROUND`).
- Map specific Canva `brand_template_id`s to each "Shadowpunk" asset type.

### 2.3 Automated Social Pipeline (`src/main.py`)
- Add a `--autofill` flag to the `generate-api` command.
- Logic: `Leonardo (Pixels) -> Canva Upload (Asset) -> Canva Autofill (Layout)`.

## ✅ Definition of Done
- A single CLI command creates a finalized, branded Canva design ready for final manual review.
- The output gallery in the Dashboard can show the final "Design ID" from Canva.
