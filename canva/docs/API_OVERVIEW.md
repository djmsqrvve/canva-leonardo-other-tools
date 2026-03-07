# Canva API Overview & Open Source Findings

Based on official documentation (canva.dev) and open-source examples (like the `canva-connect-api-starter-kit`), here is a summary of how we can integrate Canva into our internal tools (`brand`, `creative`, `helix`).

## Two Main Integration Paths

1. **Connect APIs (REST APIs)** *<- Recommended for our use cases*
   - **Purpose:** Used to integrate Canva capabilities into external platforms and scripts.
   - **Key Capabilities:**
     - **Autofill API:** Programmatically create designs by autofilling Canva templates with data (e.g., generating 100 variations of an ad from a spreadsheet).
     - **Asset Management:** Uploading images, videos, and assets directly into a Canva account folder.
     - **Design Export:** Exporting finished designs to PDF, JPG, MP4, etc.
   - **OpenAPI Spec:** Available at `https://www.canva.dev/sources/connect/api/latest/api.yml`
   - **Authentication:** OAuth 2.0 (requires `CANVA_CLIENT_ID` and `CANVA_CLIENT_SECRET`).

2. **Apps SDK**
   - **Purpose:** Used to build apps that run *inside* the Canva editor (as an iframe).
   - **Tech:** React/TypeScript.
   - **Starter Kit:** `canva-apps-sdk-starter-kit` on GitHub.

## Typical "Automated" Workflow (Connect API)

For tools like `helix` or `creative`, a common workflow using the Connect API is:
1. **Design a Template** in Canva manually.
2. **Fetch Template Details** via the API to find the editable text/image fields.
3. **Use the Autofill Endpoint** (`POST /v1/autofills`) passing the template ID and the new text/image data.
4. **Poll or Wait** for the autofill job to complete.
5. **Export the Design** (`POST /v1/exports`) and download the final asset.

## Resources
- **Developer Portal:** https://www.canva.dev/
- **Connect API Quickstart:** https://www.canva.dev/docs/connect/
- **GitHub Connect Starter Kit:** https://github.com/canva-developers/connect-api-starter-kit
