"""DEPRECATED: legacy scaffold CLI kept for reference only.

Do not add new behavior here. The maintained entrypoint is `src/main.py`.
"""

import argparse
import yaml
import os
import time
from apis.leonardo_api import LeonardoClient
from apis.canva_api import CanvaClient

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "prompts.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def generate_leonardo_asset(config, asset_key):
    prompt_data = config.get("prompts", {}).get(asset_key)
    if not prompt_data:
        raise ValueError(f"No prompt configuration found for '{asset_key}'")
    
    model_key = prompt_data.get("model")
    model_id = config.get("models", {}).get(model_key)
    if not model_id:
        raise ValueError(f"Model ID not found for key '{model_key}'")

    print(f"--- Generating {asset_key} with Leonardo.Ai ---")
    print(f"Prompt: {prompt_data['prompt']}")
    
    # In a real scenario, uncomment below to execute:
    # client = LeonardoClient()
    # urls = client.generate_and_wait(
    #     prompt=prompt_data["prompt"],
    #     model_id=model_id,
    #     width=prompt_data.get("width", 1024),
    #     height=prompt_data.get("height", 1024),
    #     alchemy=prompt_data.get("alchemy", False)
    # )
    # return urls[0] if urls else None

    # Mock return for testing CLI skeleton
    print("... (Mocking Leonardo API Call) ...")
    time.sleep(1)
    return f"https://mock.leonardo.ai/generated_{asset_key}.png"

def composite_in_canva(config, template_key, background_url):
    template_id = config.get("canva_templates", {}).get(template_key)
    if not template_id or template_id == "TEMPLATE_ID_HERE":
        print(f"Skipping Canva step: No valid template ID for '{template_key}'")
        return None

    print(f"--- Compositing in Canva (Template: {template_id}) ---")
    
    # In a real scenario, uncomment below:
    # client = CanvaClient()
    # job_id = client.autofill_template(template_id, {"Background": background_url})
    # print(f"Autofill job started: {job_id}. Polling...")
    # ... poll logic ...
    
    # Mock return for testing
    print("... (Mocking Canva API Call) ...")
    time.sleep(1)
    return "mock_canva_design_id"

def main():
    print("⚠️  Deprecated: use `python src/main.py ...` instead of `python src/cli.py ...`.")
    parser = argparse.ArgumentParser(description="DJ MSQRVVE Brand Automator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: generate
    gen_parser = subparsers.add_parser("generate", help="Generate a specific brand asset")
    gen_parser.add_argument("asset_type", choices=[
        "social_banner", "profile_avatar", "raid_alert", 
        "helix_tileset", "helix_texture", "bevy_skybox"
    ], help="Type of asset to generate")
    
    args = parser.parse_args()
    config = load_config()

    try:
        if args.command == "generate":
            if args.asset_type == "social_banner":
                img_url = generate_leonardo_asset(config, "social_banner_bg")
                design_id = composite_in_canva(config, "twitch_starting_soon", img_url)
                print(f"Success! Base art: {img_url}")
                if design_id: print(f"Canva Design ID: {design_id}")
                
            elif args.asset_type == "raid_alert":
                img_url = generate_leonardo_asset(config, "raid_alert_art")
                print(f"Success! Alert Art: {img_url}")
                # Future: Route to stream_ops/obs_assets
                
            elif args.asset_type == "bevy_skybox":
                img_url = generate_leonardo_asset(config, "bevy_skybox")
                print(f"Success! Skybox Art: {img_url}")
                # Future: Route to pipeline_scripts for Bevy conversion
            
            else:
                print(f"Pipeline for {args.asset_type} is scaffolding. Check back later!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
