import argparse
import os
import yaml
from dotenv import load_dotenv
from lib.leonardo_browser import LeonardoBrowser
from apis.leonardo_api import LeonardoClient
from apis.canva_api import CanvaClient

def load_environment():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(env_path)

def load_prompts():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "prompts.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def main():
    load_environment()
    config = load_prompts()
    
    parser = argparse.ArgumentParser(description="DJ MSQRVVE Brand System CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: generate-browser
    # For using the free 'Essential' plan via Canva login on the web UI
    browser_parser = subparsers.add_parser("generate-browser", help="Generate assets via automated browser (Free tokens)")
    browser_parser.add_argument("prompt_key", help="Key from prompts.yaml or a custom prompt string")
    browser_parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")

    # Command: generate-api
    # For using the Production API (Requires LEONARDO_API_KEY + Credits)
    api_parser = subparsers.add_parser("generate-api", help="Generate assets via Production API (Requires Credits)")
    api_parser.add_argument("asset_type", help="Asset type from prompts.yaml")

    args = parser.parse_args()

    if args.command == "generate-browser":
        # Get the prompt from prompts.yaml or use as raw string
        prompt = config.get("prompts", {}).get(args.prompt_key, {}).get("prompt", args.prompt_key)
        
        print(f"--- Starting Browser Automation Pipeline ---")
        browser = LeonardoBrowser(headless=args.headless)
        try:
            browser.login()
            image_urls = browser.generate(prompt)
            if image_urls:
                print(f"✅ Success! Retrieved {len(image_urls)} images:")
                for i, url in enumerate(image_urls):
                    print(f"   [{i}] {url}")
            else:
                print("❌ Generation failed or no images found.")
        finally:
            print("Closing browser...")
            browser.close()

    elif args.command == "generate-api":
        asset_key = args.asset_type
        prompt_data = config.get("prompts", {}).get(asset_key)
        
        if not prompt_data:
            print(f"❌ Error: No prompt configuration found for '{asset_key}' in prompts.yaml")
            return

        print(f"--- Starting Production API Pipeline for: {asset_key} ---")
        
        # 1. Leonardo Generation
        leo_client = LeonardoClient()
        model_key = prompt_data.get("model", "phoenix")
        model_id = config.get("models", {}).get(model_key)
        
        print(f"🚀 Triggering Leonardo generation (Model: {model_key})...")
        image_urls = leo_client.generate_and_wait(
            prompt=prompt_data["prompt"],
            model_id=model_id,
            width=prompt_data.get("width", 1024),
            height=prompt_data.get("height", 1024),
            alchemy=prompt_data.get("alchemy", True)
        )
        
        if not image_urls:
            print("❌ Leonardo generation failed to return image URLs.")
            return

        image_url = image_urls[0]
        print(f"✅ Leonardo Art Generated: {image_url}")

        # 2. Check for Canva Integration
        # Look for a matching template in canva_templates config
        template_id = config.get("canva_templates", {}).get(asset_key)
        
        if template_id and template_id != "TEMPLATE_ID_HERE":
            print(f"🎨 Detected Canva Integration Workflow (Template: {template_id})")
            canva_client = CanvaClient()
            
            print("🔄 Triggering Canva Autofill...")
            # We pass the generated image as the 'Background' variable
            job_id = canva_client.autofill_template(template_id, {"Background": image_url})
            
            # For brevity in this CLI, we'll output the job ID. 
            # In a full production script, we would poll for completion.
            print(f"✅ Canva Autofill Job Started: {job_id}")
            print(f"View and export your finished design in the Canva dashboard.")
        else:
            print(f"🖼  Leonardo-Only Workflow: Asset is ready at {image_url}")


if __name__ == "__main__":
    main()
