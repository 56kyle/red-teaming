#!/usr/bin/env python3
"""
Quick test script to get started with the browser automation framework.
This script demonstrates basic browser control and interaction.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from atlas_browser_target import AtlasBrowserTarget
    from test_server import TestServer
    from config import Config
except ValueError as e:
    if "OPENAI_API_KEY" in str(e):
        print("⚠️  Configuration Error:")
        print("   OPENAI_API_KEY not found in .env file")
        print("   Please edit .env and add your API key")
        print("   The quick test can still run browser automation without it")
        print()
        # Set a dummy key for browser-only testing
        import os
        os.environ["OPENAI_API_KEY"] = "sk-dummy-for-browser-test-only"
        from atlas_browser_target import AtlasBrowserTarget
        from test_server import TestServer
        from config import Config
    else:
        raise

async def quick_test():
    """Run a quick test of the browser automation."""
    print("=" * 80)
    print("🌐 Atlas Browser Automation - Quick Test")
    print("=" * 80)
    
    # Check configuration
    print("\n📋 Configuration Check:")
    print(f"  Atlas Path: {Config.ATLAS_BROWSER_PATH or '(using Chromium)'}")
    print(f"  Test Server: http://{Config.TEST_SERVER_HOST}:{Config.TEST_SERVER_PORT}")
    print(f"  Headless Mode: {Config.HEADLESS_MODE}")
    print(f"  Screenshots: {Config.SCREENSHOT_ON_INTERACTION}")
    
    # Start test server
    print("\n🚀 Starting test server...")
    server = TestServer(
        host=Config.TEST_SERVER_HOST,
        port=Config.TEST_SERVER_PORT
    )
    server.start()
    
    # Wait for server to be ready
    await asyncio.sleep(2)
    print(f"✓ Test server running at {server.get_url()}")
    
    # Initialize browser
    print("\n🌐 Launching browser...")
    browser = AtlasBrowserTarget(
        headless=Config.HEADLESS_MODE,
        slow_mo=Config.BROWSER_SLOW_MO,
        screenshot_on_interaction=Config.SCREENSHOT_ON_INTERACTION
    )
    
    try:
        await browser.launch()
        print("✓ Browser launched successfully")
        
        # Navigate to test server index
        print("\n📄 Navigating to test server...")
        index_url = server.get_url()
        await browser.navigate(index_url)
        print(f"✓ Navigated to {index_url}")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Try to navigate to a test page
        print("\n📄 Loading test page (indirect_injection)...")
        test_url = server.get_url("indirect_injection")
        await browser.navigate(test_url)
        print(f"✓ Loaded test page: {test_url}")
        
        # Extract page content
        print("\n📖 Extracting page content...")
        content = await browser.extract_page_content()
        print(f"✓ Extracted {len(content)} characters")
        print(f"  Preview: {content[:200]}...")
        
        # Try sidebar interaction (if Atlas is available)
        print("\n💬 Attempting sidebar interaction...")
        print("  (This will only work if Atlas browser is available)")
        print("  (Otherwise, you'll see a warning)")
        
        response = await browser.interact_with_sidebar(
            "Can you summarize this article for me?"
        )
        
        if response:
            print(f"✓ Got AI response: {response[:200]}...")
        else:
            print("⚠ No response received (this is normal if using Chromium)")
            print("  The framework will work with Chromium, but AI features require Atlas")
        
        # Show interactions
        print("\n📊 Browser Interactions:")
        interactions = browser.get_interactions()
        for i, interaction in enumerate(interactions, 1):
            print(f"  {i}. {interaction.action} - {interaction.page_url}")
            if interaction.screenshot_path:
                print(f"     Screenshot: {interaction.screenshot_path}")
        
        print("\n✅ Quick test completed successfully!")
        print("\nNext steps:")
        print("  1. Set OPENAI_API_KEY in .env file")
        print("  2. Set ATLAS_BROWSER_PATH if you have Atlas installed")
        print("  3. Run: python atlas_orchestrator.py")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await browser.close()
        server.stop()
        print("✓ Cleanup complete")


if __name__ == "__main__":
    try:
        asyncio.run(quick_test())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

