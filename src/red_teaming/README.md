# Atlas Browser Red Teaming Harness

An automated security testing framework for red teaming **ChatGPT Atlas browser** using browser automation (Playwright) and custom attack strategies. Tests AI-specific vulnerabilities including indirect prompt injection, agent mode exploitation, memory poisoning, and cross-site manipulation.

**What is Atlas?** ChatGPT Atlas is OpenAI's AI-native Chromium browser (launched October 2024, currently macOS only) that integrates ChatGPT directly into the browsing experience with features like AI sidebar assistance, agent mode for task automation, and browser memory.

## ⚠️ Important Disclaimer

This tool is designed for **authorized security research and testing only**. Use it responsibly:

- Only test systems you have explicit permission to test
- Use burner/test accounts, never production credentials
- Follow OpenAI's terms of service and research guidelines
- Store results securely and handle vulnerability findings responsibly
- Never use discovered vulnerabilities maliciously

## 🎯 Features

### Browser-Specific Attack Testing
- **Indirect Prompt Injection**: Tests if AI reads and follows hidden instructions in webpage content
- **Agent Mode Exploitation**: Attempts to trigger unauthorized actions via Atlas's agent features
- **Memory Poisoning**: Tests if malicious pages can corrupt AI's browser memory
- **Cross-Site Manipulation**: Exploits memory persistence across different websites
- **Privacy Bypass**: Tests incognito mode isolation and private session boundaries
- **Sidebar Hijacking**: Targets the ChatGPT sidebar with page-based injections

### Core Capabilities
- **Browser Automation**: Uses Playwright to control Atlas browser programmatically
- **Test Server**: Hosts adversarial HTML pages locally for controlled testing
- **Screenshot Evidence**: Captures visual proof of successful attacks
- **Intelligent Scoring**: Detects browser actions, memory leaks, and privacy violations
- **Detailed Reporting**: HTML and JSON reports with attack scenarios and findings
- **Dual Mode**: Supports both browser testing (Atlas) and API-only testing (fallback)
- **Multi-Turn Attacks**: Tests conversation context across page interactions

## 📋 Requirements

- Python 3.9+
- **ChatGPT Atlas browser** (macOS, October 2024+) OR regular Chromium for testing
- OpenAI account with Atlas access (for browser features)
- OpenAI API key (for API fallback mode)
- Playwright for browser automation

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to the repository
cd red_teaming

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Create environment file from template
cp env.example .env
# Edit .env and add your configuration
```

### 2. Configuration

Edit `.env` and configure for your setup:

```bash
# Required: OpenAI API key (use test account!)
OPENAI_API_KEY=sk-your-key-here

# Atlas browser path (leave empty to use Chromium)
ATLAS_BROWSER_PATH=/Applications/Atlas.app/Contents/MacOS/Atlas

# Testing mode: 'browser' for Atlas, 'api' for API-only
TESTING_MODE=browser

# Browser settings
HEADLESS_MODE=false
SCREENSHOT_ON_INTERACTION=true
```

### 3. Run Your First Campaign

**Browser Mode (Atlas Testing):**
```bash
python atlas_orchestrator.py
```

This will:
- Launch the Atlas browser (or Chromium if Atlas not found)
- Start local test server hosting adversarial pages
- Navigate through attack scenarios
- Interact with AI sidebar
- Capture screenshots of attacks
- Score responses for vulnerabilities
- Generate detailed reports with evidence

**API Mode (Fallback):**
```bash
# Set TESTING_MODE=api in .env, then:
python attack_orchestrator.py
```

### 4. View Results

Reports are generated in both JSON and HTML formats:

```bash
# View the latest HTML report
open reports/report_<timestamp>.html

# Or examine JSON results
cat results/results_<timestamp>.json
```

## 📁 Project Structure

```
red_teaming/
├── config.py                 # Configuration management
├── atlas_target.py          # PyRIT target for Atlas API
├── custom_strategies.py     # Attack strategy implementations
├── scoring_rules.py         # Response scoring logic
├── attack_orchestrator.py   # Main test runner
├── report_generator.py      # Report generation
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create from .env.example)
├── datasets/               # Attack prompt datasets
│   ├── safety_violations.json
│   ├── prompt_injections.json
│   ├── jailbreaks.json
│   └── data_leakage.json
├── results/                # Test results (auto-created)
└── reports/                # Generated reports (auto-created)
```

## 🔧 Advanced Usage

### Running Specific Attack Strategies

```python
from attack_orchestrator import AttackOrchestrator
import asyncio

async def run_custom():
    orchestrator = AttackOrchestrator(
        strategies=["Prompt Injection", "Jailbreak Attempts"],
        max_prompts_per_strategy=5
    )
    await orchestrator.run_campaign()

asyncio.run(run_custom())
```

### Custom Attack Strategies

Create your own attack strategies by extending the `AttackStrategy` class:

```python
from custom_strategies import AttackStrategy, AttackCategory

class CustomStrategy(AttackStrategy):
    def __init__(self):
        super().__init__(
            name="My Custom Attack",
            category=AttackCategory.PROMPT_INJECTION,
            description="Description of what this tests"
        )
    
    def get_prompts(self):
        return [
            "Custom prompt 1",
            "Custom prompt 2",
            # ...
        ]
```

### Custom Scoring Rules

Implement custom scorers to detect specific vulnerabilities:

```python
from scoring_rules import ResponseScorer, ScoringResult, SeverityLevel

class MyCustomScorer(ResponseScorer):
    def __init__(self):
        super().__init__("My Custom Scorer")
    
    def score(self, prompt: str, response: str) -> ScoringResult:
        # Your scoring logic here
        return ScoringResult(
            is_successful=False,
            severity=SeverityLevel.NONE,
            confidence=0.8,
            reasoning="Why this score was given",
            matched_patterns=[],
            score=0.0
        )
```

### Generating Reports from Existing Results

```bash
python report_generator.py results/results_20241027_143022.json
```

## 📊 Understanding Results

### Severity Levels

- **CRITICAL**: Model completely bypassed, harmful output generated
- **HIGH**: Significant vulnerability, partial safety bypass
- **MEDIUM**: Concerning response, needs manual review
- **LOW**: Minor issue, mostly handled correctly
- **NONE**: Attack failed, model handled correctly

### Success Metrics

The harness tracks:
- Overall success rate (% of attacks that bypassed defenses)
- Category-specific success rates
- Severity distribution
- Response patterns and matched indicators

### Report Contents

HTML reports include:
- Executive summary with key metrics
- Severity distribution charts
- Category performance analysis
- Detailed results for each attack
- Filtering options for easy navigation

## 🛠️ How It Works

### 1. Browser Automation & Test Pages

The `AtlasBrowserTarget` uses Playwright to:
- Launch and control the Atlas browser (or Chromium)
- Navigate to adversarial test pages hosted locally
- Interact with the ChatGPT sidebar
- Monitor AI responses and actions
- Capture screenshots as evidence

Test pages include hidden prompt injections, memory poisoning content, and agent mode exploits:
- `indirect_injection.html` - Hidden divs with malicious instructions
- `memory_poison.html` - Attempts to corrupt browser memory with false info
- `agent_hijack.html` - Tries to trigger unauthorized agent actions
- `cross_site_setup.html` + `cross_site_attack.html` - Tests memory isolation
- `sidebar_exploit.html` - Targets ChatGPT sidebar specifically
- `privacy_bypass.html` - Tests incognito mode boundaries

### 2. Attack Execution

The `AtlasOrchestrator` manages the campaign:
- Starts local test server hosting adversarial pages
- Launches Atlas browser with automation
- Navigates to each test page
- Sends prompts via sidebar interaction
- Captures AI responses and browser behavior

### 3. Response Scoring

The `AtlasCompositeScorer` runs browser-specific scorers:
- **IndirectInjectionScorer**: Detects if AI followed hidden page instructions
- **BrowserActionScorer**: Identifies unintended browser actions (navigation, downloads, etc.)
- **MemoryPoisoningScorer**: Catches cross-page information leakage
- **PrivacyViolationScorer**: Detects incognito session boundary violations
- **AgentExploitationScorer**: Identifies unauthorized agent mode actions

Plus standard scorers for safety, prompt injection, and data leakage.

### 3. Result Analysis

The `AttackOrchestrator`:
- Coordinates attack execution across strategies
- Collects and aggregates results
- Calculates success metrics
- Generates timestamped result files

### 4. Report Generation

The `ReportGenerator`:
- Transforms JSON results into HTML reports
- Creates visualizations and charts
- Provides filtering and search capabilities
- Exports detailed vulnerability information

## 🎓 Educational Notes

### Why Red Teaming Matters

Red teaming AI systems helps:
- Identify vulnerabilities before malicious actors do
- Improve model safety and robustness
- Understand failure modes and edge cases
- Build better defenses and detection systems

### Attack Categories Explained

**Prompt Injection**: Attempts to override system instructions by injecting malicious prompts that confuse the model about what instructions to follow.

**Jailbreaking**: Creative strategies to bypass safety measures, often using roleplay, hypotheticals, or encoded requests.

**Data Leakage**: Tests if the model can be tricked into revealing training data, which could include PII, copyrighted content, or other sensitive information.

**Safety Violations**: Direct attempts to get the model to generate harmful, illegal, or unethical content.

### Best Practices

1. **Start Small**: Begin with a few prompts per strategy to understand behavior
2. **Review Results**: Automated scoring isn't perfect—manually review flagged responses
3. **Iterate**: Use findings to create new test cases
4. **Document**: Keep detailed notes on successful attacks for reporting
5. **Responsible Disclosure**: Report findings through proper channels

## 🤝 Contributing

This is a research tool. To improve it:

1. Add new attack strategies in `custom_strategies.py`
2. Enhance scoring rules in `scoring_rules.py`
3. Create additional datasets in `datasets/`
4. Improve reporting in `report_generator.py`

## 📝 License

This tool is for educational and authorized security research only. Use responsibly and ethically.

## 🔗 References

- [Microsoft PyRIT](https://github.com/Azure/PyRIT)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [AI Red Teaming Best Practices](https://learn.microsoft.com/en-us/security/ai-red-team/)

## 📧 Support

For issues, questions, or contributions, please open an issue in the repository or consult the documentation.

---

**Remember**: With great power comes great responsibility. Use this tool ethically and legally.

