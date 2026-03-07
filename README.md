# DJ MSQRVVE // Twilight Shadowpunk Asset Pipeline

A comprehensive suite of tools for automating the generation of "Twilight Shadowpunk" branded assets for social media, live streaming, and game development.

## 🌌 Overview
This project bridges the creative power of **Leonardo.Ai** with the layout precision of **Canva Connect API**, orchestrated through a Python-based automation engine and a sleek **Next.js Dashboard**.

### Key Aesthetic: Twilight Shadowpunk
- **Themes:** Neon-Deco, Googie-Atomic, Usonian-Luxe, Masquerave-Noir.
- **Palette:** Deep twilight purples, electric teals, warm amber neon, organic mossy greens, dark noir blacks.

---

## 🛠 Project Components

### 1. Brand System CLI (`dj_msqrvve_brand_system/`)
The core Python engine for asset generation.
- **`src/main.py`**: Unified entry point for all generation tasks.
- **`src/lib/`**: Reusable modules for Leonardo API, Leonardo Browser (automation), and Canva API.
- **`config/prompts.yaml`**: The master "Shadowpunk" prompt library.

### 2. Dashboard (`dashboard/`)
A Next.js 16 control center running on **port 6767**.
- Trigger generations visually.
- Preview outputs in a "Shadowpunk" styled gallery.
- Manage both Browser-based (Free) and API-based (Production) workflows.

### 3. Stream Operations (`stream_ops/`)
- **`obs_assets/`**: HTML/CSS/JS overlays featuring animated chevron motifs and bioluminescent pulses.
- **`api_server/`**: FastAPI implementation for dynamic, AI-generated stream alerts.

### 4. Game Assets (`game_assets/`)
- Folders organized for **Helix 2000** (2D) and **Helix MAIN GAME** (3D).
- Ready for sprite atlases, PBR textures, and environmental concept art.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- Node.js 18+
- Leonardo.Ai account (linked via Canva for free tokens)
- Canva Business/Enterprise account

### Setup
1. **Initialize Python Environment:**
   ```bash
   cd dj_msqrvve_brand_system
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Configure Environment:**
   - Copy `.env.example` to `.env`.
   - Add your `LEONARDO_API_KEY`, `CANVA_CLIENT_ID`, and `CANVA_CLIENT_SECRET`.
3. **Authenticate Canva:**
   ```bash
   python src/auth_server.py
   ```
   *Follow the URL to generate your access token.*
4. **Launch Dashboard:**
   ```bash
   cd dashboard
   npm install
   npm run dev
   ```
   *Access at http://localhost:6767*

## 🧪 Testing
Run the comprehensive test suite to ensure pipeline health:
```bash
pytest dj_msqrvve_brand_system/tests/
```

---

## 📝 Documentation
For deeper technical details, see:
- `docs/DJ_MSQRVVE_RESEARCH_REPORT.md`: Full research and architecture.
- `dj_msqrvve_brand_system/DOCS.md`: CLI and library usage.
- `docs/CANVA_SETUP_GUIDE.md`: Integration setup steps.
