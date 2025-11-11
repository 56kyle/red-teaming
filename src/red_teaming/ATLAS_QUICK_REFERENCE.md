# Atlas Browser Red Teaming - Quick Reference

## 🚀 Quick Start Commands

```bash
# Validate your setup
python validate_setup.py

# Run Atlas browser tests
python atlas_orchestrator.py

# Run API-only tests (fallback)
python attack_orchestrator.py

# Start test server standalone
python test_server.py

# Test browser automation
python atlas_browser_target.py

# Test scoring rules
python atlas_scorer.py

# List available attack scenarios
python atlas_attack_strategies.py
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `atlas_orchestrator.py` | **Main entry point** for browser testing |
| `atlas_browser_target.py` | Browser automation controller |
| `atlas_attack_strategies.py` | Attack scenario definitions |
| `atlas_scorer.py` | Browser-specific vulnerability detection |
| `test_server.py` | Serves adversarial HTML pages |
| `test_pages/*.html` | 6 adversarial web pages |
| `validate_setup.py` | Setup verification |
| `env.example` | Configuration template |

## 🎯 Attack Scenarios

### Indirect Injection
Tests if AI reads hidden webpage content.
- **Test page:** indirect_injection.html
- **Vector:** Hidden divs, meta tags, HTML comments

### Memory Poisoning
Tests if pages can corrupt browser memory.
- **Test page:** memory_poison.html
- **Vector:** False credentials, trusted contacts

### Agent Hijacking
Tests if pages can trigger unauthorized actions.
- **Test page:** agent_hijack.html
- **Vector:** data-ai-action attributes, agent instructions

### Cross-Site Attack
Tests if AI leaks info between sites.
- **Test pages:** cross_site_setup.html → cross_site_attack.html
- **Vector:** Memory persistence across navigation

### Privacy Bypass
Tests incognito session isolation.
- **Test page:** privacy_bypass.html
- **Vector:** Private session data retention

### Sidebar Exploitation
Tests sidebar-specific injections.
- **Test page:** sidebar_exploit.html
- **Vector:** Multiple injection techniques

## ⚙️ Configuration Quick Reference

**env.example → .env**

```bash
# Required
OPENAI_API_KEY=sk-your-test-key-here

# Atlas browser (optional, will use Chromium if not set)
ATLAS_BROWSER_PATH=/Applications/Atlas.app/Contents/MacOS/Atlas

# Mode: 'browser' or 'api'
TESTING_MODE=browser

# Browser settings
HEADLESS_MODE=false
SCREENSHOT_ON_INTERACTION=true
BROWSER_SLOW_MO=100

# Test server
TEST_SERVER_HOST=127.0.0.1
TEST_SERVER_PORT=8888
```

## 📊 Understanding Results

### Severity Levels
- **CRITICAL** 🔴 - Complete bypass, harmful output
- **HIGH** 🟠 - Significant vulnerability
- **MEDIUM** 🟡 - Concerning behavior
- **LOW** 🟢 - Minor issue
- **NONE** ✅ - Attack defended

### Success Indicators
- `overall_success: true` = Attack succeeded
- Check `success_indicators_found` for specific patterns matched
- Review `screenshots` for visual evidence
- Examine `ai_responses` for actual AI behavior

### Results Location
```
results/
├── atlas_results_TIMESTAMP.json      # All results
├── atlas_successful_TIMESTAMP.json   # Successful attacks only
└── screenshots/                       # Visual evidence
    └── navigate_1.png
    └── sidebar_interaction_2.png
```

## 🔍 Troubleshooting

### "Atlas browser not found"
- Set `ATLAS_BROWSER_PATH` in .env to Atlas executable
- Or leave empty to use Chromium (will work but miss Atlas-specific features)

### "playwright: command not found"
```bash
pip install playwright
playwright install chromium
```

### "No response from AI sidebar"
- Sidebar selectors may need adjustment (Atlas UI changes)
- Check screenshots to see what's happening
- Try non-headless mode: `HEADLESS_MODE=false`

### "Test pages not loading"
- Check test server is running (auto-starts with orchestrator)
- Verify test_pages/ directory exists
- Check firewall isn't blocking localhost:8888

### "API key errors"
- Verify API key in .env
- Run `python validate_setup.py` to test connection
- Use test account, not production key

## 🎓 Understanding the Code

### Flow: Browser Mode
```
1. atlas_orchestrator.py starts
2. test_server.py launches (background)
3. atlas_browser_target.py opens browser
4. For each scenario:
   a. Navigate to test page
   b. Wait for load
   c. Send prompts to sidebar
   d. Capture responses
   e. Take screenshots
   f. atlas_scorer.py scores response
5. Save results with evidence
6. Cleanup (close browser, stop server)
```

### Flow: API Mode
```
1. attack_orchestrator.py starts
2. openai_api_target.py connects to API
3. For each strategy:
   a. Send prompts via API
   b. Get responses
   c. scoring_rules.py scores
4. Save results
```

## 🛡️ Safety Checklist

Before running:
- [ ] Using test/burner OpenAI account
- [ ] Not using production API key
- [ ] Have permission to test
- [ ] Results stored securely
- [ ] Will report findings responsibly

## 📈 Expected Results

**Healthy Atlas:** Most attacks should fail (NONE severity)

**Vulnerable Atlas:** May see:
- AI following hidden instructions (indirect injection)
- AI recalling cross-site info (memory poisoning)
- AI suggesting attacker URLs (agent hijacking)
- AI leaking incognito data (privacy bypass)

## 🔗 Resources

- **Atlas Announcement:** https://openai.com/index/introducing-chatgpt-atlas/
- **Playwright Docs:** https://playwright.dev/python/
- **Security Research:** Search for "indirect prompt injection AI browsers"

## 💡 Tips

1. **Start small:** Run `python validate_setup.py` first
2. **Watch it work:** Use `HEADLESS_MODE=false` to see browser
3. **Check screenshots:** Visual evidence in results/screenshots/
4. **Review logs:** Check results/red_team.log for details
5. **Test incrementally:** Run specific scenarios first before full campaign

## 📞 Getting Help

1. Run validation: `python validate_setup.py`
2. Check logs: `cat results/red_team.log`
3. Review IMPLEMENTATION_COMPLETE.md for architecture
4. Check README.md for detailed documentation

---

**Remember:** This is for authorized security research only. Use responsibly!

