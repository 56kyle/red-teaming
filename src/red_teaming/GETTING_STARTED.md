# Getting Started with Browser Automation Framework

Quick guide to get you up and running with the Atlas browser red teaming framework.

## Prerequisites

- Python 3.9 or higher
- macOS (for Atlas browser) or any OS (for Chromium fallback)
- OpenAI API key (get one at https://platform.openai.com/api-keys)

## Step 1: Install Dependencies

### Option A: Using pip (recommended for quick start)

```bash
cd src/red_teaming
pip3 install -r requirements.txt
playwright install chromium
```

### Option B: Using uv (if you have it)

```bash
cd /Users/krisciu/workspace/red-teaming
uv pip install -r src/red_teaming/requirements.txt
playwright install chromium
```

## Step 2: Configure Environment

1. **Edit the `.env` file** in `src/red_teaming/`:

```bash
cd src/red_teaming
nano .env  # or use your favorite editor
```

2. **Set your OpenAI API key** (required):
```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

3. **Optional: Set Atlas browser path** (if you have Atlas installed):
```bash
ATLAS_BROWSER_PATH=/Applications/Atlas.app/Contents/MacOS/Atlas
```

4. **Configure testing mode**:
   - `TESTING_MODE=browser` - Full browser automation (requires Atlas or Chromium)
   - `TESTING_MODE=api` - API-only testing (no browser needed)

## Step 3: Quick Test

Run the quick test script to verify everything works:

```bash
cd src/red_teaming
python3 quick_test.py
```

This will:
- Start a local test server
- Launch a browser (Chromium if Atlas not found)
- Navigate to a test page
- Try to interact with the sidebar
- Show you what's working

**Expected output:**
- ✅ Test server starts successfully
- ✅ Browser launches
- ✅ Test page loads
- ⚠️ Sidebar interaction may fail if using Chromium (this is normal)

## Step 4: Run Your First Campaign

Once the quick test works, run a full campaign:

```bash
python3 atlas_orchestrator.py
```

This will:
- Execute all attack scenarios
- Test browser-specific vulnerabilities
- Generate results and screenshots
- Create detailed reports

## Understanding the Output

### Results Location

- **JSON Results**: `results/atlas_results_YYYYMMDD_HHMMSS.json`
- **Successful Attacks**: `results/atlas_successful_YYYYMMDD_HHMMSS.json`
- **Screenshots**: `results/screenshots/`
- **Logs**: `results/red_team.log`

### Campaign Summary

After a campaign, you'll see:
```
Campaign Summary
================
Total Attacks: 15
Successful Attacks: 2
Success Rate: 13.33%
Duration: 245.67 seconds

Severity Breakdown:
  🔴 CRITICAL: 1
  🟠 HIGH: 1
  🟡 MEDIUM: 0
  🟢 LOW: 0
```

## Common Issues & Solutions

### Issue: "OPENAI_API_KEY not found"
**Solution**: Make sure you've set `OPENAI_API_KEY` in your `.env` file

### Issue: "ModuleNotFoundError: No module named 'playwright'"
**Solution**: Run `pip3 install playwright && playwright install chromium`

### Issue: "Atlas browser path not found, using Chromium"
**Solution**: This is fine! The framework works with Chromium. If you have Atlas, set `ATLAS_BROWSER_PATH` in `.env`

### Issue: "No response received from AI"
**Solution**: 
- If using Chromium: This is expected - Chromium doesn't have AI sidebar
- If using Atlas: Check that Atlas is running and sidebar is accessible

### Issue: "Test server port already in use"
**Solution**: Change `TEST_SERVER_PORT` in `.env` to a different port (e.g., 8889)

## Next Steps

### Explore Attack Scenarios

View all available attack scenarios:
```python
from atlas_attack_strategies import list_all_scenarios
list_all_scenarios()
```

### Run Specific Scenarios

```python
from atlas_orchestrator import AtlasOrchestrator
import asyncio

async def test_specific():
    orchestrator = AtlasOrchestrator(
        scenarios=["Hidden Prompt Injection via Display:None"]
    )
    await orchestrator.run_campaign()

asyncio.run(test_specific())
```

### Customize Test Pages

Edit HTML files in `test_pages/` to create your own attack vectors.

### Add Custom Scorers

Extend the scoring engine in `atlas_scorer.py` to detect new vulnerability patterns.

## Tips for Best Results

1. **Start Small**: Run quick_test.py first to verify setup
2. **Use Visible Browser**: Set `HEADLESS_MODE=false` initially to see what's happening
3. **Check Screenshots**: Review screenshots in `results/screenshots/` to understand interactions
4. **Review Logs**: Check `results/red_team.log` for detailed execution information
5. **Experiment**: Modify test pages and scenarios to test your own ideas

## Need Help?

- Check `README.md` for detailed documentation
- Review `ARCHITECTURE.md` for system design
- Look at `example_usage.py` for code examples
- Check logs in `results/red_team.log`

---

**Happy Testing! 🚀**

