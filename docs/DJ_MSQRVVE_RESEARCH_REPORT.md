# DJ MSQRVVE // TWILIGHT SHADOWPUNK ASSET PIPELINE

## CONTEXT & IDENTITY
**Brand:** DJ MSQRVVE
**Aesthetic:** Twilight Shadowpunk (Blade Runner meets bioluminescent nature / Sleepywood mystique)
**Architecture:** Cyberpunk Wright / Inverted Googie Organic Forms
**Themes:** Neon-Deco, Googie-Atomic, Usonian-Luxe, Masquerave-Noir
**Motifs:** Corner Chevrons, Orbit Glows, Bioluminescent Tech
**Vibe:** Polished vibes without cringe. Confident, playful, evolved.
**Color Palette:** Deep twilight purples, electric teals, warm amber neon, organic mossy greens, dark noir blacks with glowing edges

---

## 1. SOCIAL MEDIA ASSETS

### 1. Research Summary
To establish a cohesive "Twilight Shadowpunk" brand across platforms, standardizing asset dimensions is crucial. Automating the generation and assembly of these assets requires combining the Leonardo.Ai Creative Engine API (for base art and textures) and the Canva Connect API (for typography, templated layouts, and final compositing). 
**Key Tools:** 
- **Canva Connect API:** Designs API for generating and exporting designs from Brand Templates.
- **Leonardo.Ai API:** For generating backgrounds, character art, and texture sheets using models like Leonardo Phoenix or Kino.

**Optimal Sizes:**
- **Twitch:** Profile (256x256), Panels (320x160), Overlays (1920x1080), Banner (1200x480).
- **YouTube:** Channel Art (2560x1440), Thumbnails (1280x720), Shorts Covers (1080x1920).
- **Twitter/X:** Header (1500x500), Post (1200x675).
- **Discord:** Server Banner (960x540), Role Icons (64x64), Emoji (128x128).

### 2. Step-by-Step Implementation Guide
1. **Design Templates:** Create "Twilight Shadowpunk" Brand Templates in Canva for all required sizes. Use placeholders for background images and text.
2. **Setup API Credentials:** Obtain Canva Connect API and Leonardo.Ai API keys.
3. **Generate Base Art:** Use Leonardo.Ai API to generate base imagery (e.g., bioluminescent backgrounds, neon-deco patterns).
4. **Composite in Canva:** Use the Canva Connect API to pass the Leonardo-generated images and dynamic text (e.g., "Stream Starting Soon") into the Canva Brand Templates.
5. **Export & Post:** Export the finalized design from Canva via API and post to social channels or update profiles.

### 3. Code Samples (Python)
```python
import requests
import time

# Pseudo-code for Leonardo -> Canva pipeline
LEONARDO_API_KEY = "your_leonardo_key"
CANVA_API_KEY = "your_canva_key"

def generate_leonardo_background(prompt):
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    headers = {"Authorization": f"Bearer {LEONARDO_API_KEY}"}
    payload = {
        "prompt": prompt,
        "modelId": "6b645e3a-d64f-4341-a6d8-7aa363f858d3", # Example Model ID
        "width": 1920,
        "height": 1080,
        "alchemy": True
    }
    response = requests.post(url, json=payload, headers=headers).json()
    # Poll for completion and return image URL...
    return "https://leonardo.ai/generated_image_url.png"

def create_canva_design(template_id, background_url, text):
    url = "https://api.canva.com/rest/v1/designs"
    headers = {"Authorization": f"Bearer {CANVA_API_KEY}"}
    payload = {
        "design_type": "template",
        "asset_id": template_id,
        "variables": {
            "Background": background_url,
            "TitleText": text
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
```

### 4. Prompt Templates for Leonardo.Ai
- **Social Banner Background:** "Twilight shadowpunk cityscape, inverted googie organic forms, deep twilight purples and electric teals, bioluminescent tech glowing in the dark noir blacks, neon-deco style, cinematic lighting, 8k resolution, highly detailed."
- **Profile Avatar:** "Cyberpunk character portrait, masquerave-noir theme, wearing a bioluminescent mask, warm amber neon highlights, sleepywood mystique, polished and confident, masterpiece, vivid colors."

### 5. Recommended File Structure
```
/assets
  /social_media
    /templates
      twitch_banner_template.json
      youtube_thumbnail_template.json
    /generated
      /backgrounds
      /composites
```

---

## 2. OBS LIVE STREAMING SETTINGS & ALERTS

### 1. Research Summary
For a visually striking "Twilight Shadowpunk" stream, OBS needs a multi-layered scene architecture. Alerts and dynamic elements can be driven by a local Python FastAPI server that uses Leonardo.Ai to generate unique assets on the fly. HTML/CSS/JS browser sources are ideal for animated motifs (chevrons, orbit glows).
**Key Tools:** 
- **OBS Studio (Ubuntu 26.04/PipeWire):** Core streaming software.
- **Python FastAPI:** Local webhook receiver and API orchestrator.
- **HTML/CSS/JS:** Custom animated overlays.

### 2. Step-by-Step Implementation Guide
1. **OBS Architecture:** Create nested scenes. Base Scene (Game/Camera) -> Overlay Scene (HUD, Chevrons, Chat) -> Alert Scene (Browser source for FastAPI alerts).
2. **Develop Browser Sources:** Build HTML/CSS pages using CSS animations (glows, pulses, chevron sliding) matching the color palette.
3. **Build FastAPI Server:** Create a Python server to receive webhooks from StreamElements or Twitch.
4. **Dynamic Alert Generation:** On receiving a raid webhook, call Leonardo API to generate custom "Masquerave-Noir" art based on the raider's name, then send it via WebSocket to the OBS browser source alert overlay.
5. **OBS Settings:** Use NVENC (if available) or VAAPI for hardware encoding on Ubuntu. Set to 1080p60, 6000kbps bitrate. Ensure hardware acceleration is enabled for browser sources.

### 3. Code Samples (HTML/CSS/JS for Overlay & Python FastAPI)
**HTML/CSS (Animated Chevron Overlay):**
```html
<style>
  .chevron {
    width: 50px; height: 50px;
    border-right: 5px solid #00FFFF; /* Electric Teal */
    border-bottom: 5px solid #00FFFF;
    transform: rotate(-45deg);
    animation: pulseGlow 2s infinite, slideRight 3s linear infinite;
    box-shadow: 2px 2px 10px #8A2BE2; /* Deep Purple Glow */
  }
  @keyframes pulseGlow { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; box-shadow: 2px 2px 20px #8A2BE2; } }
</style>
<div class="chevron"></div>
```

**Python FastAPI (Alert Server):**
```python
from fastapi import FastAPI, WebSocket
import asyncio

app = FastAPI()
clients = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        clients.remove(websocket)

@app.post("/webhook/raid")
async def handle_raid(payload: dict):
    raider = payload.get("username", "Unknown")
    # Call Leonardo API for dynamic art here...
    image_url = "https://leonardo.ai/raid_art.png" 
    
    # Broadcast to OBS Browser Source
    for client in clients:
        await client.send_json({"type": "raid", "user": raider, "image": image_url})
    return {"status": "success"}
```

### 4. Prompt Templates for Leonardo.Ai
- **Dynamic Raid Alert:** "A glowing neon sign displaying bioluminescent tech, masquerave-noir style, deep twilight purples and warm amber neon, cyberpunk wright architecture background, celebration mood, high quality."
- **Follower Alert Icon:** "A small glowing orb, organic mossy greens and electric teals, sleepywood mystique, subtle orbit glow, isolated on black background."

### 5. Recommended File Structure
```
/stream_ops
  /obs_assets
    /overlays
      hud.html
      styles.css
    /alerts
      alert_receiver.html
  /api_server
    main.py
```

---

## 3. IN-GAME ASSETS (Helix 2000 + Helix MAIN GAME)

### 1. Research Summary
**Helix 2000 (2D):** Requires pixel or painterly 2D assets. Leonardo.Ai can generate sprite sheets and tilesets using specific models tuned for 2D game art.
**Helix MAIN GAME (3D) & Roblox:** Requires texture maps (albedo, normal) and concept art. Leonardo.Ai is excellent for generating seamless textures and environmental concepts. Canva can be used to layout UI elements before exporting to Roblox or Vite.
**Key Tools:** Leonardo.Ai API (for textures/sprites), Canva API (for UI layouts).

### 2. Step-by-Step Implementation Guide
1. **2D Sprites (Helix 2000):** Use Leonardo API to generate character frames in a grid. Use Python to slice the grid into individual frames and pack them into a texture atlas for Colyseus/Vite.
2. **3D Textures (Helix MAIN):** Request seamless textures from Leonardo (e.g., "seamless mossy cyberpunk metal"). Use tools like Materialize (or custom Python OpenCV scripts) to generate normal and roughness maps from the albedo image.
3. **UI Assets (Roblox/Vite):** Generate UI panel backgrounds and icons with Leonardo. Import to Canva via API, apply "Twilight Shadowpunk" typography and borders, export as transparent PNGs.

### 3. Code Samples (Python Atlas Packer)
```python
from PIL import Image
import os

def slice_leonardo_spritesheet(image_path, rows, cols, output_dir):
    img = Image.open(image_path)
    width, height = img.size
    frame_w = width // cols
    frame_h = height // rows
    
    os.makedirs(output_dir, exist_ok=True)
    count = 0
    for r in range(rows):
        for c in range(cols):
            box = (c * frame_w, r * frame_h, (c + 1) * frame_w, (r + 1) * frame_h)
            frame = img.crop(box)
            frame.save(f"{output_dir}/frame_{count:03d}.png")
            count += 1
```

### 4. Prompt Templates for Leonardo.Ai
- **Helix 2000 Tileset:** "2D game isometric tileset, sleepywood mystique, bioluminescent organic mossy greens, dark noir stone paths, pixel art hybrid, highly detailed, seamless."
- **Helix MAIN Texture:** "Seamless texture, usonian-luxe architecture panel, glowing electric teal lines, deep twilight purple base, PBR material base, high resolution."
- **UI Element:** "Sci-fi HUD panel background, corner chevrons, googie-atomic style, dark translucent noir black with neon glowing edges, UI asset."

### 5. Recommended File Structure
```
/game_assets
  /helix_2000
    /sprites
      /raw_generations
      /atlases
    /ui
  /helix_main
    /textures
      /albedo
      /normals
    /concept_art
```

---

## 4. GAME ENGINE ASSETS (Bevy / Rust + Helix Custom Engine)

### 1. Research Summary
Integrating generated assets into a Rust/Bevy engine requires an automated pipeline to handle formatting, resizing, and manifest generation. Python scripts can manage the Leonardo API calls and post-processing, outputting directly to the Bevy `/assets` folder. Canva can serve as the design layer for HUDs.
**Key Tools:** Python (ImageMagick/Pillow for processing), Bevy Engine, Leonardo API.

### 2. Step-by-Step Implementation Guide
1. **Asset Request Script:** Run a Python script requesting specific Bevy assets (e.g., skyboxes, particle textures) from Leonardo.
2. **Post-Processing Pipeline:** The Python script downloads the image, resizes it to power-of-two dimensions (required for many 3D engines), converts it to optimized formats (like `.ktx2` or `.webp`), and generates associated `.meta` files for Bevy.
3. **UI Handoff:** Design HUD elements in Canva. Export them via Canva API. A Python script reads the Canva export, splits it into 9-slice scalable UI textures, and saves them to the Bevy asset folder.

### 3. Code Samples (Python Pre-processor for Bevy)
```python
from PIL import Image

def process_texture_for_bevy(input_path, output_path):
    img = Image.open(input_path)
    
    # Ensure power of two sizing
    def next_power_of_two(x):
        return 1 if x == 0 else 2**(x - 1).bit_length()
    
    new_w = next_power_of_two(img.width)
    new_h = next_power_of_two(img.height)
    
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)
    
    # Save as optimized PNG or WebP
    img_resized.save(output_path, format="PNG", optimize=True)
    
    # Generate mock .meta file for Bevy (if needed)
    with open(output_path + ".meta", "w") as f:
        f.write('{"format": "png", "sampler": "linear"}')
```

### 4. Prompt Templates for Leonardo.Ai
- **Bevy Skybox:** "360 degree equirectangular panorama skybox, deep twilight purples, massive inverted googie organic forms in the distance, neon-deco cityscape, glowing orbit rings in the sky, 8k resolution."
- **Particle Texture:** "Bioluminescent magic effect, glowing spark, deep purple and electric teal, isolated on black background, perfect for additive blending."

### 5. Recommended File Structure
```
/bevy_project
  /assets
    /textures
      /environment
      /ui
    /sprites
/pipeline_scripts
  generate_skybox.py
  process_ui.py
```

---

## 5. BRAND AUTOMATION SYSTEM (The Full Pipeline)

### 1. Research Summary
The ultimate goal is a unified CLI or orchestration script that manages all brand assets. It routes requests based on `content_type`, interacts with Leonardo for imagery, Canva for composition, and local utilities for post-processing.
**Key Tools:** Python (Click/Typer for CLI), requests library, API wrappers.

### 2. Step-by-Step Implementation Guide
1. **Build the CLI:** Use a Python library like `argparse` or `Click` to create commands (e.g., `python brand_system.py generate twitch_panel`).
2. **Define Content Handlers:** Create specific handler functions for each content type. A `social_banner` handler will call Leonardo -> Canva -> Export. A `game_sprite` handler will call Leonardo -> Image Splitter -> Atlas Packer.
3. **Centralize Prompt Library:** Store all "Twilight Shadowpunk" prompt templates in a JSON or YAML configuration file.
4. **Configure Canva Templates:** Maintain a mapping of `content_type` to Canva Brand Template IDs in the configuration file.

### 3. Code Samples (Python CLI Orchestrator)
```python
import argparse
import json

def load_config():
    return {
        "twitch_panel": {"prompt_key": "neon_panel", "canva_template": "TMP_123"},
        "game_sprite": {"prompt_key": "pixel_char", "pipeline": "slice_and_pack"}
    }

def main():
    parser = argparse.ArgumentParser(description="DJ MSQRVVE Brand Automator")
    parser.add_argument("action", choices=["generate"])
    parser.add_argument("content_type", choices=["twitch_panel", "alert_art", "game_sprite", "social_banner"])
    
    args = parser.parse_args()
    config = load_config()
    
    if args.action == "generate":
        target = config.get(args.content_type)
        print(f"Starting pipeline for {args.content_type}...")
        
        # Step 1: Leonardo Generation
        # image_url = generate_leonardo(...)
        
        # Step 2: Routing based on config
        if "canva_template" in target:
            print(f"Routing to Canva template {target['canva_template']}...")
            # composite_in_canva(...)
        elif "pipeline" in target:
            print(f"Routing to local pipeline {target['pipeline']}...")
            # process_locally(...)
            
        print("Asset generated and saved to /assets!")

if __name__ == "__main__":
    main()
```

### 4. Prompt Templates for Leonardo.Ai (Library Excerpts)
- **ID 001 (Base Vibe):** "Twilight shadowpunk, deep twilight purples, electric teals, warm amber neon, dark noir blacks, bioluminescent nature."
- **ID 002 (Architecture):** "Cyberpunk Wright architecture, inverted googie organic forms, usonian-luxe interiors."
- **ID 003 (UI Motifs):** "Corner chevrons, orbit glows, sleek neon-deco borders, transparent HUD elements."

### 5. Recommended File Structure
```
/dj_msqrvve_brand_system
  /config
    prompts.yaml
    templates.json
  /src
    cli.py
    leonardo_client.py
    canva_client.py
    image_processor.py
  /assets_out
    /social
    /stream
    /game
```
