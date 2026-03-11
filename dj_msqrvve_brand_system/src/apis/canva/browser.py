"""Canva editor automation via headless Firefox."""
from __future__ import annotations

import time
from pathlib import Path

from lib.browser.driver import BrowserBase

try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
except ModuleNotFoundError:
    By = None  # type: ignore[assignment,misc]
    EC = None  # type: ignore[assignment,misc]
    ActionChains = None  # type: ignore[assignment,misc]

CANVA_HOME = "https://www.canva.com/"
EDITOR_LOAD_TIMEOUT = 30


class CanvaBrowser(BrowserBase):
    """Thin automation layer over the Canva web editor."""

    SITE_NAME = "Canva"

    def __init__(self, headless: bool = True, **kwargs):
        super().__init__(headless=headless, **kwargs)
        self.driver.set_window_size(1920, 1080)

    # -- navigation --

    def open_home(self) -> None:
        self.driver.get(CANVA_HOME)
        time.sleep(3)
        if self.is_auth_page():
            self.raise_session_expired("canva-home", "Not logged into Canva.")

    def open_design(self, edit_url: str) -> None:
        """Open a Canva design by its edit URL (from the API)."""
        self.driver.get(edit_url)
        self._wait_for_editor()

    def _wait_for_editor(self, timeout: int = EDITOR_LOAD_TIMEOUT) -> None:
        """Wait until the Canva editor canvas is interactive."""
        from selenium.webdriver.support.ui import WebDriverWait

        wait = WebDriverWait(self.driver, timeout)
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[class*='canvasContainer'], [data-testid='canvas-container'], canvas")
        ))
        time.sleep(2)  # let the editor JS finish hydrating

    # -- sidebar navigation --

    def click_sidebar(self, tab_name: str) -> None:
        """Click a sidebar tab by accessible name: Templates, Elements, Text, Uploads, etc."""
        self.driver.execute_script("""
            const name = arguments[0].toLowerCase();
            const buttons = Array.from(document.querySelectorAll('button, [role="tab"]'));
            for (const btn of buttons) {
                const label = (btn.getAttribute('aria-label') || btn.innerText || '').toLowerCase().trim();
                if (label === name) {
                    btn.click();
                    return true;
                }
            }
            return false;
        """, tab_name)
        time.sleep(1.5)

    # -- template application --

    def apply_template(self, index: int = 0) -> None:
        """Click a template thumbnail from the Templates sidebar panel.

        Opens the Templates tab if not already open, then clicks the nth thumbnail.
        """
        self.click_sidebar("Templates")
        time.sleep(2)
        thumbnails = self.driver.find_elements(
            By.CSS_SELECTOR, "[class*='template'] img, [data-testid*='template'] img"
        )
        if index < len(thumbnails):
            thumbnails[index].click()
            time.sleep(3)

    # -- image placement --

    def open_uploads(self) -> None:
        self.click_sidebar("Uploads")
        time.sleep(1.5)

    def upload_image(self, file_path: str | Path) -> None:
        """Upload a local image file via the Uploads panel file input."""
        self.open_uploads()
        file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(str(Path(file_path).resolve()))
        time.sleep(5)  # wait for upload to complete

    def click_first_upload(self) -> None:
        """Click the first image in the Uploads panel to place it on the canvas."""
        self.open_uploads()
        images = self.driver.find_elements(By.CSS_SELECTOR, "[class*='uploads'] img, [class*='upload'] img")
        if images:
            images[0].click()
            time.sleep(2)

    def drag_upload_to_canvas(self, upload_index: int = 0) -> None:
        """Drag an uploaded image from the sidebar onto the center of the canvas."""
        self.open_uploads()
        images = self.driver.find_elements(By.CSS_SELECTOR, "[class*='uploads'] img, [class*='upload'] img")
        if upload_index >= len(images):
            return
        source = images[upload_index]
        canvas = self.driver.find_element(
            By.CSS_SELECTOR, "[class*='canvasContainer'], [data-testid='canvas-container'], canvas"
        )
        ActionChains(self.driver).drag_and_drop(source, canvas).perform()
        time.sleep(2)

    # -- text --

    def add_heading(self, text: str) -> None:
        """Add a heading text element via the Text sidebar panel."""
        self.click_sidebar("Text")
        time.sleep(1)
        self.driver.execute_script("""
            const text = arguments[0].toLowerCase();
            const buttons = Array.from(document.querySelectorAll('button'));
            for (const btn of buttons) {
                if ((btn.innerText || '').toLowerCase().includes('add a heading')) {
                    btn.click();
                    return true;
                }
            }
            return false;
        """, text)
        time.sleep(2)
        # Type the actual text
        active = self.driver.switch_to.active_element
        active.send_keys(text)
        time.sleep(1)

    def add_subheading(self, text: str) -> None:
        self.click_sidebar("Text")
        time.sleep(1)
        self.driver.execute_script("""
            const buttons = Array.from(document.querySelectorAll('button'));
            for (const btn of buttons) {
                if ((btn.innerText || '').toLowerCase().includes('add a subheading')) {
                    btn.click();
                    return true;
                }
            }
            return false;
        """)
        time.sleep(2)
        active = self.driver.switch_to.active_element
        active.send_keys(text)
        time.sleep(1)

    # -- canvas state --

    def get_page_count(self) -> int:
        text = self.driver.find_element(By.TAG_NAME, "body").text
        # Look for "X / Y" pattern in the page footer
        import re
        match = re.search(r"(\d+)\s*/\s*(\d+)", text)
        if match:
            return int(match.group(2))
        return 1

    def screenshot_canvas(self, name: str = "canva_canvas") -> str:
        return self.screenshot(name)
