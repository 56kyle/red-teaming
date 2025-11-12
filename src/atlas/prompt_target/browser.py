"""Module containing logic for prompting against the atlas browser."""
import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List
from typing import List
from typing import Optional
from typing import Optional
from typing import Optional
from typing import Optional
from typing import Optional
from typing import Optional
from typing import Optional
from typing import Optional

from playwright.async_api import Browser
from playwright.async_api import BrowserContext
from playwright.async_api import Page
from playwright.async_api import async_playwright

from pyrit.prompt_target import PromptTarget

from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.atlas_browser_target import logger
from red_teaming.config import Config
from red_teaming.config import Config
from red_teaming.config import Config
from red_teaming.config import Config
from red_teaming.config import Config
from red_teaming.config import Config
from red_teaming.config import Config


@dataclass
class BrowserInteraction:
    """Represents an interaction with the Atlas browser."""
    timestamp: str
    page_url: str
    action: str  # navigate, click, type, etc.
    target: str  # element or URL
    ai_response: Optional[str] = None
    screenshot_path: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class AtlasBrowserTarget:
    """
    Controls ChatGPT Atlas browser for red teaming.

    Tests Atlas-specific features:
    - Indirect prompt injection via webpage content
    - Agent mode exploitation
    - Browser memory poisoning
    - Cross-site AI manipulation
    - Sidebar interaction hijacking
    """

    def __init__(
        self,
        headless: bool = False,
        slow_mo: int = 100,
        screenshot_on_interaction: bool = True,
    ):
        """
        Initialize Atlas browser controller.

        Args:
            headless: Run browser in headless mode
            slow_mo: Slow down operations by N milliseconds (useful for debugging)
            screenshot_on_interaction: Take screenshots after each interaction
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.screenshot_on_interaction = screenshot_on_interaction

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self.interactions: List[BrowserInteraction] = []
        self.screenshot_counter = 0

        # Atlas-specific selectors (may need adjustment based on actual Atlas UI)
        self.selectors = {
            "chatgpt_sidebar": "[data-testid='chatgpt-sidebar']",
            "chat_input": "[data-testid='chat-input']",
            "chat_message": "[data-testid='chat-message']",
            "agent_mode_toggle": "[data-testid='agent-mode-toggle']",
            "memory_settings": "[data-testid='memory-settings']",
        }

    async def launch(self) -> None:
        """Launch the Atlas browser."""
        logger.info("Launching Atlas browser...")

        self.playwright = await async_playwright().start()

        # Try to launch Atlas if path is specified, otherwise use Chromium
        if Config.ATLAS_BROWSER_PATH and Path(Config.ATLAS_BROWSER_PATH).exists():
            logger.info(f"Launching Atlas from: {Config.ATLAS_BROWSER_PATH}")
            self.browser = await self.playwright.chromium.launch(
                executable_path=Config.ATLAS_BROWSER_PATH,
                headless=self.headless,
                slow_mo=self.slow_mo,
            )
        else:
            logger.warning("Atlas browser path not found, using Chromium")
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
            )

        # Create browser context with specific settings
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            record_video_dir=str(Config.RESULTS_DIR / "videos") if Config.RECORD_BROWSER_VIDEO else None,
        )

        self.page = await self.context.new_page()

        # Set up console message capture
        self.page.on("console", lambda msg: logger.debug(f"Browser console: {msg.text}"))

        logger.info("Atlas browser launched successfully")

    async def close(self) -> None:
        """Close the browser and cleanup."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        logger.info("Browser closed")

    async def navigate(self, url: str) -> BrowserInteraction:
        """
        Navigate to a URL.

        Args:
            url: URL to navigate to

        Returns:
            BrowserInteraction with navigation details
        """
        if not self.page:
            await self.launch()

        logger.info(f"Navigating to: {url}")

        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for page to be fully loaded
            await asyncio.sleep(2)

            screenshot_path = None
            if self.screenshot_on_interaction:
                screenshot_path = await self._take_screenshot(f"navigate_{self.screenshot_counter}")

            interaction = BrowserInteraction(
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                page_url=url,
                action="navigate",
                target=url,
                screenshot_path=screenshot_path,
                success=True
            )

            self.interactions.append(interaction)
            return interaction

        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            interaction = BrowserInteraction(
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                page_url=url,
                action="navigate",
                target=url,
                success=False,
                error=str(e)
            )
            self.interactions.append(interaction)
            return interaction

    async def interact_with_sidebar(self, prompt: str) -> Optional[str]:
        """
        Send a prompt to the ChatGPT sidebar and get response.

        Args:
            prompt: Prompt to send to ChatGPT

        Returns:
            AI response text or None if failed
        """
        if not self.page:
            raise RuntimeError("Browser not launched. Call launch() first.")

        logger.info(f"Interacting with sidebar: {prompt[:50]}...")

        try:
            # Try to find and click the ChatGPT sidebar
            # Note: These selectors are guesses and need to be adjusted based on actual Atlas UI
            try:
                await self.page.wait_for_selector(self.selectors["chat_input"], timeout=5000)
            except:
                logger.warning("ChatGPT sidebar not visible, attempting to open it")
                # Try common ways to open sidebar
                try:
                    await self.page.keyboard.press("Command+K")  # Common shortcut
                    await asyncio.sleep(1)
                except:
                    pass

            # Type the prompt
            chat_input = await self.page.wait_for_selector(self.selectors["chat_input"], timeout=5000)
            await chat_input.fill(prompt)
            await chat_input.press("Enter")

            # Wait for response
            await asyncio.sleep(3)  # Give AI time to respond

            # Try to capture the response
            try:
                messages = await self.page.query_selector_all(self.selectors["chat_message"])
                if messages:
                    last_message = messages[-1]
                    response_text = await last_message.inner_text()

                    if self.screenshot_on_interaction:
                        await self._take_screenshot(f"sidebar_interaction_{self.screenshot_counter}")

                    logger.info(f"Got AI response: {response_text[:100]}...")
                    return response_text
            except Exception as e:
                logger.error(f"Failed to capture AI response: {e}")

            return None

        except Exception as e:
            logger.error(f"Sidebar interaction failed: {e}")
            return None

    async def enable_agent_mode(self) -> bool:
        """
        Enable Agent mode in Atlas.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Attempting to enable Agent mode...")

        try:
            # This is speculative - actual implementation depends on Atlas UI
            toggle = await self.page.wait_for_selector(
                self.selectors["agent_mode_toggle"],
                timeout=5000
            )
            await toggle.click()
            await asyncio.sleep(1)

            logger.info("Agent mode enabled")
            return True

        except Exception as e:
            logger.warning(f"Could not enable Agent mode: {e}")
            return False

    async def extract_page_content(self) -> str:
        """
        Extract the current page's text content.

        Returns:
            Page text content
        """
        if not self.page:
            return ""

        try:
            content = await self.page.content()
            text = await self.page.evaluate("() => document.body.innerText")
            return text
        except Exception as e:
            logger.error(f"Failed to extract page content: {e}")
            return ""

    async def inject_content(self, html: str) -> bool:
        """
        Inject HTML content into the current page (for testing).

        Args:
            html: HTML content to inject

        Returns:
            True if successful
        """
        try:
            await self.page.evaluate(f"document.body.innerHTML += `{html}`")
            return True
        except Exception as e:
            logger.error(f"Content injection failed: {e}")
            return False

    async def _take_screenshot(self, name: str) -> str:
        """Take a screenshot and return the path."""
        self.screenshot_counter += 1
        screenshot_path = Config.RESULTS_DIR / "screenshots" / f"{name}_{self.screenshot_counter}.png"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)

        await self.page.screenshot(path=str(screenshot_path), full_page=True)
        logger.debug(f"Screenshot saved: {screenshot_path}")

        return str(screenshot_path)

    async def wait_for_ai_response(self, timeout: int = 10) -> Optional[str]:
        """
        Wait for AI to respond in the sidebar.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            AI response text or None
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Check for new messages
                messages = await self.page.query_selector_all(self.selectors["chat_message"])
                if messages:
                    last_message = messages[-1]
                    text = await last_message.inner_text()
                    if text:
                        return text
            except:
                pass

            await asyncio.sleep(0.5)

        return None

    def get_interactions(self) -> List[BrowserInteraction]:
        """Get all browser interactions from this session."""
        return self.interactions

    def clear_interactions(self) -> None:
        """Clear interaction history."""
        self.interactions = []
        self.screenshot_counter = 0
