# Architecture Overview

This document explains how the red teaming harness works under the hood.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Attack Orchestrator                         │
│  (Coordinates campaigns, manages execution flow)             │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌──────────────┐        ┌──────────────┐
│   Attack     │        │   Atlas      │
│  Strategies  │───────▶│   Target     │
│              │        │  (PyRIT)     │
└──────────────┘        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  OpenAI API  │
                        │  (Atlas)     │
                        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │   Scoring    │
                        │   Engine     │
                        └──────┬───────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
        ┌──────────────┐            ┌──────────────┐
        │   Results    │            │   Report     │
        │   Storage    │            │  Generator   │
        └──────────────┘            └──────────────┘
```

## Component Details

### 1. Configuration Layer (`config.py`)

**Purpose**: Centralized configuration management

**Key Features**:
- Loads environment variables from `.env`
- Validates API keys and credentials
- Creates necessary directories
- Provides default values
- Type-safe configuration access

**How it works**:
```python
# Configuration is validated on import
from config import Config

# Access settings
api_key = Config.OPENAI_API_KEY
model = Config.ATLAS_MODEL
```

### 2. Atlas Target (`atlas_target.py`)

**Purpose**: Bridge between PyRIT framework and Atlas API

**Key Features**:
- Implements PyRIT's `PromptTarget` interface
- Handles async communication with OpenAI API
- Manages conversation history for multi-turn attacks
- Implements rate limiting
- Error handling and recovery

**How it works**:
1. Receives prompt from PyRIT
2. Applies rate limiting (respects API quotas)
3. Builds message array (includes conversation history if multi-turn)
4. Sends request to OpenAI API
5. Captures response
6. Returns structured result to PyRIT

**Rate Limiting Logic**:
```python
# Ensures minimum time between requests
min_interval = 60.0 / REQUESTS_PER_MINUTE
if time_since_last < min_interval:
    await asyncio.sleep(min_interval - time_since_last)
```

### 3. Attack Strategies (`custom_strategies.py`)

**Purpose**: Define adversarial prompts organized by attack type

**Strategy Categories**:
- **Safety Violations**: Content policy bypass attempts
- **Prompt Injections**: System prompt extraction
- **Data Leakage**: PII and training data extraction
- **Jailbreaks**: Advanced restriction bypass
- **Bias & Fairness**: Demographic and political bias
- **Hallucinations**: False information generation

**How it works**:
```python
class AttackStrategy:
    def __init__(self, name, category, description):
        # Store metadata
        pass
    
    def get_prompts(self) -> List[str]:
        # Return list of attack prompts
        pass
```

**Extensibility**:
Users can easily add new strategies by:
1. Creating a subclass of `AttackStrategy`
2. Implementing `get_prompts()` method
3. Adding to `AVAILABLE_STRATEGIES` list

### 4. Scoring Engine (`scoring_rules.py`)

**Purpose**: Automated evaluation of model responses

**Scorer Types**:

1. **SafetyViolationScorer**
   - Pattern matching for harmful content
   - Detects refusal language
   - Identifies hedging behavior

2. **PromptInjectionScorer**
   - Detects system prompt exposure
   - Identifies instruction override
   - Checks for suspicious compliance

3. **DataLeakageScorer**
   - Regex patterns for PII (email, phone, SSN)
   - API key detection
   - Memorization indicators

4. **JailbreakScorer**
   - Composite scoring (combines safety + injection)
   - Adaptive severity classification

**Scoring Process**:
```
Input: (prompt, response)
    ↓
Run all scorers in parallel
    ↓
Each scorer returns: ScoringResult
    ↓
Composite scorer picks worst result
    ↓
Output: Overall severity + success flag
```

**Severity Classification**:
- Score 0.0-0.2 → NONE (safe)
- Score 0.2-0.4 → LOW (minor concern)
- Score 0.4-0.6 → MEDIUM (needs review)
- Score 0.6-0.8 → HIGH (significant issue)
- Score 0.8-1.0 → CRITICAL (complete bypass)

### 5. Attack Orchestrator (`attack_orchestrator.py`)

**Purpose**: Main execution engine that coordinates testing

**Execution Flow**:

```
1. Initialize
   - Create AtlasTarget
   - Load CompositeScorer
   - Select strategies to run

2. Collect Prompts
   - Gather from all selected strategies
   - Apply max_prompts_per_strategy limit
   - Calculate total workload

3. Execute Campaign
   For each strategy:
       For each prompt:
           - Reset conversation
           - Send to Atlas
           - Score response
           - Log result
           - Update progress bar

4. Generate Summary
   - Calculate success rates
   - Categorize by severity
   - Break down by category

5. Save Results
   - JSON results file
   - Separate file for successful attacks
   - Timestamped filenames
```

**Progress Tracking**:
Uses `tqdm` for real-time progress visualization:
```
Running attacks: 45%|████████      | 27/60 [02:15<02:45, 5.00s/it]
```

**Error Handling**:
- Individual attack failures don't stop the campaign
- Errors are logged but execution continues
- Graceful degradation

### 6. Report Generator (`report_generator.py`)

**Purpose**: Transform results into actionable insights

**Report Types**:

1. **HTML Report**
   - Executive summary with key metrics
   - Visual charts (severity distribution, category performance)
   - Detailed attack results with syntax highlighting
   - Interactive filtering (all/successful/critical/high)
   - Scoring details for successful attacks

2. **JSON Report**
   - Machine-readable format
   - Full details for each attack
   - Programmatic analysis
   - Integration with other tools

**HTML Report Structure**:
```html
├── Header (timestamp, model, duration)
├── Executive Summary (cards with key metrics)
├── Severity Distribution (bar chart)
├── Category Performance (bar chart)
├── Filter Buttons (interactive)
└── Detailed Results
    └── For each attack:
        ├── Metadata (strategy, category, severity)
        ├── Prompt (with syntax highlighting)
        ├── Response (with syntax highlighting)
        └── Scoring Details (expandable)
```

## Data Flow

### Single Attack Execution

```
1. AttackOrchestrator selects prompt
        ↓
2. Creates PromptRequestResponse object
        ↓
3. AtlasTarget.send_prompt_async()
        ↓
4. Rate limiting check
        ↓
5. Build messages (+ conversation history if multi-turn)
        ↓
6. OpenAI API call
        ↓
7. Response captured
        ↓
8. Update conversation history
        ↓
9. CompositeScorer.score_all()
        ↓
10. Run all scorers in parallel
        ↓
11. Select worst result
        ↓
12. Create AttackResult object
        ↓
13. Append to results list
        ↓
14. Continue to next prompt
```

### Multi-Turn Attack Flow

```
Turn 1: Initial prompt → Response A
        ↓
        Conversation history: [user: prompt, assistant: response A]
        ↓
Turn 2: Follow-up prompt → Response B
        ↓
        Conversation history: [turn 1..., user: follow-up, assistant: response B]
        ↓
Turn N: ...continues until MAX_CONVERSATION_TURNS
```

## Extension Points

### Adding New Attack Strategies

1. Create subclass in `custom_strategies.py`:
```python
class MyNewStrategy(AttackStrategy):
    def __init__(self):
        super().__init__(
            name="My Attack",
            category=AttackCategory.PROMPT_INJECTION,
            description="What this tests"
        )
    
    def get_prompts(self):
        return ["prompt1", "prompt2"]
```

2. Add to registry:
```python
AVAILABLE_STRATEGIES.append(MyNewStrategy())
```

### Adding New Scorers

1. Create subclass in `scoring_rules.py`:
```python
class MyCustomScorer(ResponseScorer):
    def __init__(self):
        super().__init__("My Scorer")
    
    def score(self, prompt, response):
        # Your logic here
        return ScoringResult(...)
```

2. Add to CompositeScorer:
```python
self.scorers["my_scorer"] = MyCustomScorer()
```

### Custom Targets

To test different models/APIs:

1. Subclass `PromptTarget` from PyRIT
2. Implement `send_prompt_async()`
3. Handle authentication and API specifics
4. Use in orchestrator:
```python
orchestrator = AttackOrchestrator()
orchestrator.target = MyCustomTarget()
```

## Performance Considerations

### Rate Limiting

**Why**: Prevent API quota exhaustion and rate limit errors

**Implementation**:
- Tracks time between requests
- Async sleep to maintain minimum interval
- Configurable via `REQUESTS_PER_MINUTE`

**Trade-off**: Speed vs. compliance
- Higher rate = faster completion, more errors
- Lower rate = slower completion, safer

### Async Architecture

**Benefits**:
- Non-blocking I/O during API calls
- Better resource utilization
- Scalable to concurrent requests (future enhancement)

**Current State**:
- Sequential execution (one at a time)
- Rate limiting enforced
- Ready for parallel execution (set `MAX_CONCURRENT_REQUESTS`)

### Memory Management

**Results Storage**:
- Results accumulate in memory during campaign
- Saved to disk at completion
- For very large campaigns (1000+ prompts), consider batching

**Conversation History**:
- Limited to `MAX_CONVERSATION_TURNS * 2` messages
- Prevents token overflow
- Automatically truncates old messages

## Security Considerations

### API Key Protection

- Never commit `.env` to version control
- `.gitignore` includes `.env`
- Use burner accounts for testing
- Rotate keys regularly

### Results Storage

- Results may contain successful exploits
- Store in secure location
- Consider encryption for sensitive findings
- Implement access controls

### Responsible Use

The framework includes safeguards:
- Disclaimers in documentation
- Warnings in output
- Requires explicit configuration
- No "one-click" attack mode

But ultimately relies on user responsibility.

## Testing Strategy

### Gradual Approach

1. **Start Small**: Test with 1-2 prompts per strategy
2. **Analyze**: Review results, understand patterns
3. **Iterate**: Refine strategies based on findings
4. **Scale**: Expand to full dataset

### Continuous Testing

- Regular automated campaigns
- Compare results over time
- Track regression (new vulnerabilities)
- Monitor fix effectiveness

### Manual Review

Automated scoring isn't perfect:
- Review "successful" attacks manually
- Check "failed" attacks for false negatives
- Update scoring rules based on findings

## Future Enhancements

Potential improvements:

1. **Parallel Execution**: Use `asyncio.gather()` for concurrent attacks
2. **Adaptive Strategies**: Learn from successful attacks, generate variations
3. **Conversation Trees**: Multi-turn with branching paths
4. **Real-time Dashboard**: Live monitoring during campaigns
5. **Integration**: CI/CD pipeline integration
6. **Model Comparison**: Test multiple models simultaneously
7. **Defense Testing**: Evaluate safety filter effectiveness
8. **Mutation Engine**: Automatically generate prompt variations

## Conclusion

This architecture provides:
- **Modularity**: Easy to extend and customize
- **Scalability**: Ready for large campaigns
- **Maintainability**: Clear separation of concerns
- **Usability**: Simple interface, detailed reports
- **Safety**: Built-in protections and warnings

The system is designed for security researchers to systematically evaluate AI systems while following responsible disclosure practices.

