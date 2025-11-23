import asyncio
import json
import os
import sys
import subprocess
import time
from typing import List

# Add src/ to path so we can import red_teaming modules
sys.path.append(os.path.join(os.getcwd(), 'src'))
sys.path.append(os.path.join(os.getcwd(), 'src', 'red_teaming'))

from red_teaming.atlas_attack_strategies import BrowserAttackScenario, AtlasAttackCategory

def load_json_prompts(file_path: str) -> List[str]:
    """Extracts user prompts from the Chat Completion JSON format."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    prompts = []
    for item in data['items']:
        if item['role'] == 'user':
            for content_part in item['content']:
                if content_part['type'] == 'input_text':
                    prompts.append(content_part['text'])
    return prompts

def applescript_type(text: str):
    """Uses macOS AppleScript to type text into the focused window."""
    # Escape quotes for AppleScript
    safe_text = text.replace('\\', '\\\\').replace('"', '\\"')
    
    script = f'''
    tell application "System Events"
        set frontmost of process "ChatGPT Atlas" to true
    end tell
    delay 1.0
    tell application "System Events"
        keystroke "{safe_text}"
        delay 0.5
        keystroke return
    end tell
    '''
    
    process = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        print(f"      ❌ AppleScript Error: {stderr.decode()}")
    else:
        print("      ✅ Text injected via AppleScript")

def applescript_screenshot(filename: str):
    """Takes a screenshot of the ChatGPT window."""
    # Uses screencapture CLI
    path = os.path.abspath(f"results/screenshots/{filename}.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # -l captures the window with the ID (hard to get), -x mutes sound
    # Fallback to main screen capture for hackathon speed
    subprocess.run(['screencapture', '-x', path])
    print(f"      📸 Screenshot saved to {path}")

async def run_native_reproduction():
    print("🚀 Starting Native Mac Automation (AppleScript)...")
    
    # 1. Load Scenarios
    ss13_prompts = load_json_prompts('data/prompt_ideas/ss13_sourcing_v2.json')
    wiki_prompts = load_json_prompts('data/prompt_ideas/agent_wiki_degrees_v2.json')
    
    scenarios = [
        BrowserAttackScenario(
            name="SS13 Sourcing V2",
            category=AtlasAttackCategory.INDIRECT_INJECTION,
            description="SS13 Sourcing verification",
            test_page="",
            interaction_prompts=ss13_prompts,
            expected_safe_behavior="",
            success_indicators=[]
        ),
        BrowserAttackScenario(
            name="Wiki Degrees Supply Chain V2",
            category=AtlasAttackCategory.AGENT_EXPLOITATION,
            description="Wiki Degrees verification",
            test_page="",
            interaction_prompts=wiki_prompts,
            expected_safe_behavior="",
            success_indicators=[]
        )
    ]

    print(f"\n🛑 MANUAL ACTION REQUIRED")
    print("Ensure the ChatGPT Atlas App is OPEN and you are SIGNED IN.")
    print("👉 Starting in 5 seconds... SWITCH TO ATLAS APP IF NEEDED")
    time.sleep(5)

    for scenario in scenarios:
        print(f"\n▶️ Running Scenario: {scenario.name}")
        
        # Open a new chat (Cmd+N) - Using System Events force activation
        subprocess.run(['osascript', '-e', 'tell application "System Events" to set frontmost of process "ChatGPT Atlas" to true', '-e', 'delay 1', '-e', 'tell application "System Events" to keystroke "n" using command down'])
        time.sleep(2)
        
        for i, prompt in enumerate(scenario.interaction_prompts):
            print(f"   🗣️ Turn {i+1}: Injecting prompt...")
            
            # Type the prompt using AppleScript
            applescript_type(prompt)
            
            print("   ⏳ Waiting for generation (20s)...")
            time.sleep(20) # Wait for response
            
        print(f"   📸 Capturing final state...")
        applescript_screenshot(f"native_{scenario.name.replace(' ', '_')}")
        
    print("\n✅ Native Reproduction Complete.")

if __name__ == "__main__":
    asyncio.run(run_native_reproduction())

