# DJ MSQRVVE Brand System - Tools & Automation

This document outlines the reusable tools and helper scripts developed for the **Twilight Shadowpunk** asset pipeline.

## 🛠 Project Structure

- `src/lib/`: Reusable core libraries.
  - `canva_api.py`: Official Canva Connect API wrapper (authenticated via `.env`).
  - `leonardo_api.py`: Official Leonardo.Ai Production API wrapper (authenticated via `.env`).
  - `leonardo_browser.py`: Browser-based automation for Leonardo.ai (uses Selenium + Chrome Profile).
- `src/main.py`: The central CLI entry point for the brand system.
- `src/auth_server.py`: Local OAuth server to handle Canva authentication and token generation.
- `user_profile/`: Persistent Chrome profile directory used by browser automation to maintain logins (e.g., Canva SSO).

## 🚀 Key Workflows

### 1. Canva Authentication
To generate your `CANVA_ACCESS_TOKEN`:
```bash
python src/auth_server.py
```
*Note: Ensure `http://127.0.0.1:5000/oauth/callback` is in your Canva Redirect URLs.*

### 2. Automated Generation (Browser Route)
To generate assets using your free tokens (from the Canva Essential plan) without needing the Production API key:
```bash
python src/main.py generate-browser "your prompt"
```
- **Login:** On the first run, the browser will open. Log in via Canva.
- **Session:** Subsequent runs will use the saved session in `/user_profile`.

### 3. API-Based Generation (Production Route)
If you have a `LEONARDO_API_KEY` and credits:
```bash
python src/main.py generate-api --asset "social_banner"
```

## 🧪 Testing
Run the unit tests to ensure the libraries are healthy:
```bash
pytest tests/
```
