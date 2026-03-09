import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

class LeonardoBrowser:
    """
    Automated browser for Leonardo.ai.
    Uses a persistent Chrome profile to maintain sessions (e.g., Canva SSO).
    """
    def __init__(self, headless=False):
        # Path to the persistent Chrome profile
        profile_path = os.path.join(os.path.dirname(__file__), "..", "..", "user_profile")
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument(f"user-data-dir={profile_path}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Avoid detection as a bot (simplified)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 30)

    def login(self):
        """
        Opens the login page. If not logged in, allows manual SSO via Canva.
        """
        print("Navigating to Leonardo login...")
        self.driver.get("https://app.leonardo.ai/auth/login")
        
        # Check if already logged in (by checking for elements on the dashboard)
        try:
            # If we see the 'Generate' button or similar, we're likely logged in.
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Generate')]")))
            print("Successfully logged in (detected dashboard).")
        except:
            print("NOT logged in. Please log in manually in the browser window.")
            # Keep browser open for user to log in
            while True:
                try:
                    self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Generate')]")))
                    print("Login detected! Proceeding...")
                    break
                except:
                    time.sleep(2)

    def generate(self, prompt, model_id=None):
        """
        Automates typing a prompt and clicking generate in the web UI.
        """
        print(f"Triggering generation for prompt: '{prompt[:50]}...'")
        self.driver.get("https://app.leonardo.ai/image-generation")
        
        # Wait for the prompt input area
        try:
            # Find the prompt textarea (selector might need updates)
            prompt_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder*='Type a prompt']")))
            
            # Clear and type the prompt
            prompt_input.clear()
            prompt_input.send_keys(prompt)
            
            # Click the Generate button
            generate_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Generate')]")))
            generate_btn.click()
            
            print("Generate button clicked! Waiting for results...")
            
            # Wait for the new images to appear in the gallery
            # (Simple sleep for now to allow generation time)
            time.sleep(30)
            
            # Retrieve the latest image URLs
            images = self.driver.find_elements(By.CSS_SELECTOR, "img.generation-image")
            urls = [img.get_attribute("src") for img in images[:4]]
            return urls
            
        except Exception as e:
            print(f"Error during generation: {e}")
            return []

    def close(self):
        self.driver.quit()
