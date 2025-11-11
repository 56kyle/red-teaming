"""
Configuration management for the red teaming harness.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Central configuration class for the red teaming harness."""
    
    # Project paths
    BASE_DIR = Path(__file__).parent
    RESULTS_DIR = BASE_DIR / os.getenv("RESULTS_DIR", "results")
    REPORTS_DIR = BASE_DIR / os.getenv("REPORTS_DIR", "reports")
    DATASETS_DIR = BASE_DIR / "datasets"
    TEST_PAGES_DIR = BASE_DIR / "test_pages"
    
    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    # Atlas Browser Configuration
    ATLAS_BROWSER_PATH = os.getenv("ATLAS_BROWSER_PATH", "")
    TESTING_MODE = os.getenv("TESTING_MODE", "browser")  # 'browser' or 'api'
    
    # Model Configuration
    ATLAS_MODEL = os.getenv("ATLAS_MODEL", "gpt-4")
    ATLAS_MAX_TOKENS = int(os.getenv("ATLAS_MAX_TOKENS", "4096"))
    ATLAS_TEMPERATURE = float(os.getenv("ATLAS_TEMPERATURE", "0.7"))
    
    # Rate Limiting
    REQUESTS_PER_MINUTE = int(os.getenv("REQUESTS_PER_MINUTE", "20"))
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
    
    # Browser Automation Settings
    HEADLESS_MODE = os.getenv("HEADLESS_MODE", "false").lower() == "true"
    BROWSER_SLOW_MO = int(os.getenv("BROWSER_SLOW_MO", "100"))
    SCREENSHOT_ON_INTERACTION = os.getenv("SCREENSHOT_ON_INTERACTION", "true").lower() == "true"
    RECORD_BROWSER_VIDEO = os.getenv("RECORD_BROWSER_VIDEO", "false").lower() == "true"
    FALLBACK_BROWSER = os.getenv("FALLBACK_BROWSER", "chromium")
    
    # Test Server Configuration
    TEST_SERVER_HOST = os.getenv("TEST_SERVER_HOST", "127.0.0.1")
    TEST_SERVER_PORT = int(os.getenv("TEST_SERVER_PORT", "8888"))
    
    # Attack Configuration
    TEST_AGENT_MODE = os.getenv("TEST_AGENT_MODE", "true").lower() == "true"
    TEST_MEMORY_FEATURES = os.getenv("TEST_MEMORY_FEATURES", "true").lower() == "true"
    TEST_PRIVACY_MODE = os.getenv("TEST_PRIVACY_MODE", "true").lower() == "true"
    PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "30"))
    DELAY_BETWEEN_TESTS = int(os.getenv("DELAY_BETWEEN_TESTS", "2"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = RESULTS_DIR / os.getenv("LOG_FILE", "red_team.log")
    
    # Test Configuration
    ENABLE_MULTI_TURN = os.getenv("ENABLE_MULTI_TURN", "true").lower() == "true"
    MAX_CONVERSATION_TURNS = int(os.getenv("MAX_CONVERSATION_TURNS", "10"))
    TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "60"))
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration and create necessary directories."""
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not found. Please set it in .env file or environment variables."
            )
        
        # Create necessary directories
        cls.RESULTS_DIR.mkdir(exist_ok=True)
        cls.REPORTS_DIR.mkdir(exist_ok=True)
        cls.DATASETS_DIR.mkdir(exist_ok=True)
        cls.TEST_PAGES_DIR.mkdir(exist_ok=True)
        (cls.RESULTS_DIR / "screenshots").mkdir(exist_ok=True, parents=True)
        (cls.RESULTS_DIR / "videos").mkdir(exist_ok=True, parents=True)
        
        # Ensure log directory exists
        cls.LOG_FILE.parent.mkdir(exist_ok=True, parents=True)
    
    @classmethod
    def get_summary(cls) -> str:
        """Get a summary of the current configuration."""
        mode_str = "🌐 Browser Mode (Atlas)" if cls.TESTING_MODE == "browser" else "🔌 API Mode"
        atlas_path = cls.ATLAS_BROWSER_PATH if cls.ATLAS_BROWSER_PATH else "(using Chromium)"
        
        return f"""
Atlas Red Teaming Configuration:
---------------------------------
Mode: {mode_str}
Atlas Path: {atlas_path}
Model: {cls.ATLAS_MODEL}
Max Tokens: {cls.ATLAS_MAX_TOKENS}
Temperature: {cls.ATLAS_TEMPERATURE}

Rate Limiting:
  Requests/min: {cls.REQUESTS_PER_MINUTE}
  Max Concurrent: {cls.MAX_CONCURRENT_REQUESTS}

Browser Settings:
  Headless: {cls.HEADLESS_MODE}
  Screenshots: {cls.SCREENSHOT_ON_INTERACTION}
  Video Recording: {cls.RECORD_BROWSER_VIDEO}

Testing Features:
  Agent Mode: {cls.TEST_AGENT_MODE}
  Memory Tests: {cls.TEST_MEMORY_FEATURES}
  Privacy Tests: {cls.TEST_PRIVACY_MODE}
  Multi-turn: {cls.ENABLE_MULTI_TURN}

Directories:
  Results: {cls.RESULTS_DIR}
  Reports: {cls.REPORTS_DIR}
  Test Pages: {cls.TEST_PAGES_DIR}

Test Server:
  URL: http://{cls.TEST_SERVER_HOST}:{cls.TEST_SERVER_PORT}
"""

# Validate configuration on import
Config.validate()

