"""
Setup validation script for Atlas Red Teaming Harness.
Run this to verify your configuration before starting tests.
"""
import sys
import os
from pathlib import Path
import subprocess


def print_header(text):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def print_check(name, status, message=""):
    """Print a check result."""
    icon = "✅" if status else "❌"
    print(f"{icon} {name}")
    if message:
        print(f"   {message}")


def check_python_version():
    """Check Python version."""
    print_header("Python Environment")
    
    version = sys.version_info
    is_ok = version >= (3, 9)
    print_check(
        "Python Version",
        is_ok,
        f"Python {version.major}.{version.minor}.{version.micro}" +
        ("" if is_ok else " (Need 3.9+)")
    )
    return is_ok


def check_dependencies():
    """Check if required packages are installed."""
    print_header("Dependencies")
    
    required = {
        "playwright": "Browser automation",
        "flask": "Test server",
        "openai": "OpenAI API",
        "python-dotenv": "Configuration",
        "tqdm": "Progress bars",
        "jinja2": "Report generation",
    }
    
    all_ok = True
    for package, description in required.items():
        try:
            __import__(package.replace("-", "_"))
            print_check(f"{package}", True, description)
        except ImportError:
            print_check(f"{package}", False, f"{description} - NOT INSTALLED")
            all_ok = False
    
    return all_ok


def check_playwright_browsers():
    """Check if Playwright browsers are installed."""
    print_header("Playwright Browsers")
    
    try:
        result = subprocess.run(
            ["playwright", "install", "--dry-run", "chromium"],
            capture_output=True,
            text=True
        )
        is_installed = "is already installed" in result.stdout or result.returncode == 0
        
        print_check(
            "Chromium Browser",
            is_installed,
            "Installed" if is_installed else "Not installed - run: playwright install chromium"
        )
        return is_installed
    except FileNotFoundError:
        print_check("Playwright CLI", False, "playwright command not found")
        return False


def check_configuration():
    """Check configuration file."""
    print_header("Configuration")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    # Check if .env exists
    if env_file.exists():
        print_check(".env file", True, "Configuration file found")
        
        # Try to load and check key settings
        try:
            from dotenv import dotenv_values
            config = dotenv_values(env_file)
            
            # Check API key
            api_key = config.get("OPENAI_API_KEY", "")
            has_api_key = api_key and api_key != "sk-your-api-key-here" and len(api_key) > 20
            print_check(
                "OpenAI API Key",
                has_api_key,
                "Configured" if has_api_key else "Not set or using example value"
            )
            
            # Check testing mode
            mode = config.get("TESTING_MODE", "browser")
            print_check("Testing Mode", True, f"Set to: {mode}")
            
            # Check Atlas path if in browser mode
            if mode == "browser":
                atlas_path = config.get("ATLAS_BROWSER_PATH", "")
                if atlas_path:
                    atlas_exists = Path(atlas_path).exists()
                    print_check(
                        "Atlas Browser Path",
                        atlas_exists,
                        f"{atlas_path}" + ("" if atlas_exists else " - File not found")
                    )
                else:
                    print_check(
                        "Atlas Browser Path",
                        True,
                        "Not set (will use Chromium)"
                    )
            
            return has_api_key
            
        except Exception as e:
            print_check("Configuration Loading", False, f"Error: {e}")
            return False
    else:
        print_check(".env file", False, "Not found")
        if env_example.exists():
            print(f"   💡 Copy env.example to .env and configure it")
        return False


def check_directories():
    """Check required directories."""
    print_header("Directories")
    
    required_dirs = {
        "test_pages": "Adversarial HTML pages",
        "results": "Test results (auto-created)",
        "reports": "HTML reports (auto-created)",
        "datasets": "Attack datasets",
    }
    
    all_ok = True
    for dir_name, description in required_dirs.items():
        dir_path = Path(dir_name)
        exists = dir_path.exists()
        
        if not exists and dir_name in ["results", "reports"]:
            # Auto-create output directories
            dir_path.mkdir(exist_ok=True)
            exists = True
        
        print_check(dir_name, exists, description)
        if not exists:
            all_ok = False
    
    return all_ok


def check_test_pages():
    """Check if test pages exist."""
    print_header("Test Pages")
    
    test_pages_dir = Path("../../tests/data/test_pages")
    if not test_pages_dir.exists():
        print_check("test_pages directory", False, "Directory not found")
        return False
    
    required_pages = [
        "indirect_injection.html",
        "memory_poison.html",
        "agent_hijack.html",
        "cross_site_setup.html",
        "cross_site_attack.html",
        "sidebar_exploit.html",
        "privacy_bypass.html",
    ]
    
    all_ok = True
    for page in required_pages:
        page_path = test_pages_dir / page
        exists = page_path.exists()
        print_check(page, exists)
        if not exists:
            all_ok = False
    
    return all_ok


def test_api_connection():
    """Test OpenAI API connection."""
    print_header("API Connection Test")
    
    try:
        from openai import OpenAI
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "sk-your-api-key-here":
            print_check("API Connection", False, "API key not configured")
            return False
        
        print("Testing API connection...")
        client = OpenAI(api_key=api_key)
        
        # Try a minimal API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        
        print_check("API Connection", True, "Successfully connected to OpenAI")
        return True
        
    except Exception as e:
        print_check("API Connection", False, f"Error: {str(e)[:100]}")
        return False


def main():
    """Run all validation checks."""
    print("\n" + "=" * 70)
    print("  🔍 Atlas Red Teaming Harness - Setup Validation")
    print("=" * 70)
    
    results = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "Playwright Browsers": check_playwright_browsers(),
        "Configuration": check_configuration(),
        "Directories": check_directories(),
        "Test Pages": check_test_pages(),
    }
    
    # Optional API test
    print("\n💡 Testing API connection (optional, requires configured API key)...")
    test_api_connection()
    
    # Summary
    print_header("Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"Checks passed: {passed}/{total}\n")
    
    if passed == total:
        print("🎉 All checks passed! You're ready to run red teaming tests.")
        print("\nNext steps:")
        print("  1. Start browser testing: python atlas_orchestrator.py")
        print("  2. Or API testing: python attack_orchestrator.py")
        print("\n⚠️  Remember: Use test accounts only, never production!")
    else:
        print("⚠️  Some checks failed. Please fix the issues above before proceeding.")
        print("\nCommon fixes:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Install browsers: playwright install chromium")
        print("  - Create config: cp env.example .env")
        print("  - Edit .env and add your API key")
    
    print("\n" + "=" * 70 + "\n")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

