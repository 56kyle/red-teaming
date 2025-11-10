# Quick Start Guide

Get up and running with the Atlas Red Teaming Harness in 5 minutes.

## 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

## 2. Configure API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# Replace 'your_api_key_here' with your actual key
```

Your `.env` should look like:
```
OPENAI_API_KEY=sk-your-actual-key-here
ATLAS_MODEL=gpt-4
REQUESTS_PER_MINUTE=20
```

## 3. Run Your First Test

### Option A: Run Everything (Quick Script)
```bash
./run_tests.sh
```

### Option B: Run Manually
```bash
python attack_orchestrator.py
```

### Option C: Run Specific Examples
```bash
python example_usage.py
```

## 4. View Results

Results are saved in two formats:

**JSON Results** (machine-readable):
```bash
ls results/
cat results/results_*.json | jq .
```

**HTML Reports** (human-readable):
```bash
# Generate report
python report_generator.py results/results_TIMESTAMP.json

# Open in browser
open reports/report_TIMESTAMP.html
```

## Common Use Cases

### Test Only Prompt Injections
```python
from attack_orchestrator import AttackOrchestrator
import asyncio

async def test_injections():
    orchestrator = AttackOrchestrator(
        strategies=["Prompt Injection"],
        max_prompts_per_strategy=5
    )
    await orchestrator.run_campaign()

asyncio.run(test_injections())
```

### Quick Safety Check (Limited Prompts)
```python
from attack_orchestrator import AttackOrchestrator
import asyncio

async def quick_test():
    orchestrator = AttackOrchestrator(
        max_prompts_per_strategy=3  # Only 3 prompts per strategy
    )
    await orchestrator.run_campaign()

asyncio.run(quick_test())
```

### Test with Custom Prompts
Create a new file `my_prompts.json` in `datasets/`:
```json
{
  "name": "My Custom Tests",
  "prompts": [
    "Your custom test prompt 1",
    "Your custom test prompt 2"
  ]
}
```

Then load and test in Python:
```python
import json
from custom_strategies import AttackStrategy, AttackCategory

# Load your prompts
with open('datasets/my_prompts.json') as f:
    data = json.load(f)

# Create strategy
class MyStrategy(AttackStrategy):
    def __init__(self):
        super().__init__("My Tests", AttackCategory.PROMPT_INJECTION, "Custom tests")
    
    def get_prompts(self):
        return data['prompts']
```

## Configuration Options

Edit `.env` to customize:

| Variable | Description | Default |
|----------|-------------|---------|
| `ATLAS_MODEL` | Model to test | `gpt-4` |
| `REQUESTS_PER_MINUTE` | Rate limit | `20` |
| `MAX_CONCURRENT_REQUESTS` | Parallel requests | `5` |
| `ENABLE_MULTI_TURN` | Multi-turn attacks | `true` |
| `MAX_CONVERSATION_TURNS` | Max turns per conversation | `10` |

## Understanding Results

### Severity Levels
- **CRITICAL** 🔴: Complete bypass, harmful output
- **HIGH** 🟠: Significant vulnerability
- **MEDIUM** 🟡: Concerning, needs review
- **LOW** 🟢: Minor issue
- **NONE** ✅: Attack failed

### Success Indicators
- Look for `"overall_success": true` in JSON results
- HTML report highlights successful attacks in red
- Focus on CRITICAL and HIGH severity findings

## Troubleshooting

### "OPENAI_API_KEY not found"
Make sure you:
1. Created `.env` file (copy from `.env.example`)
2. Added your API key without quotes
3. Restarted your terminal/Python session

### Rate Limit Errors
Reduce `REQUESTS_PER_MINUTE` in `.env`:
```
REQUESTS_PER_MINUTE=10
```

### Import Errors
Make sure PyRIT is installed:
```bash
pip install pyrit
```

### No Results Generated
Check that the `results/` directory exists and is writable:
```bash
mkdir -p results reports
```

## Safety Reminders

⚠️ **IMPORTANT**:
- Only test systems you have permission to test
- Use a burner/test API key, never production
- Handle results securely (they may contain vulnerabilities)
- Follow responsible disclosure practices
- Never use findings maliciously

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore attack strategies in `custom_strategies.py`
- Customize scoring rules in `scoring_rules.py`
- Check out `example_usage.py` for more patterns
- Review sample datasets in `datasets/`

## Getting Help

Common commands:
```bash
# Check Python version (need 3.9+)
python --version

# Verify dependencies installed
pip list | grep pyrit

# Test configuration
python -c "from config import Config; print(Config.get_summary())"

# List available files
ls -la
```

Happy (ethical) hacking! 🔐

