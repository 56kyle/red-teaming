# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository is a multi-module project for red-teaming OpenAI's Atlas browser. It combines:

1. **src/atlas**: Python package for programmatic interaction with Atlas (Playwright, Selenium, OpenAI API)
2. **joestuff/red_teaming**: PyRIT-based red teaming harness with attack strategies and scoring engines
3. **terraform**: AWS infrastructure (Mac2 instance) for running Atlas in a controlled environment

The project uses modern Python tooling (Pydantic, Typer, Playwright, Selenium) with a monorepo structure and comprehensive testing framework.

## Project Structure

```
red-teaming/
├── src/atlas/                 # Main Python package for Atlas interaction
│   ├── __main__.py           # CLI entry point (Typer)
│   ├── agent.py              # [New] Agent implementation
│   ├── api.py                # OpenAI API wrapper for conversations
│   ├── constants.py          # App paths, platform-specific config
│   ├── interact.py           # GUI automation (Playwright/Selenium)
│   ├── demo.py               # Demo utilities & conversation management
│   ├── parse.py              # Parse conversation data
│   ├── process.py            # Atlas process management
│   └── _typing.py            # Type definitions & validation
│
├── joestuff/red_teaming/      # PyRIT-based attack framework [legacy]
│   ├── attack_orchestrator.py
│   ├── custom_strategies.py
│   ├── scoring_rules.py
│   └── datasets/             # JSON attack prompt datasets
│
├── terraform/                 # AWS infrastructure
├── tests/                     # Test suite
│   ├── unit_tests/
│   ├── integration_tests/
│   └── acceptance_tests/
│
└── pyproject.toml            # Modern Python project config (uv-based)
```

## Key Technologies

- **Python 3.9+**: Core language, async-first
- **Pydantic 2.x**: Data validation & settings management
- **Typer**: CLI framework
- **Playwright & Selenium**: Browser automation for Atlas GUI
- **OpenAI Python Client**: Conversations API integration
- **PyRIT** (joestuff): Red teaming framework
- **Pytest**: Testing framework with separate suites
- **Loguru**: Structured logging
- **DuckDB & Polars**: Data processing

## Common Development Commands

### Setup & Installation

```bash
# Initialize environment with uv (recommended)
uv sync

# Or with pip (older method)
pip install -e ".[dev]"
```

### Development Workflow

```bash
# Run tests
pytest                           # All tests
pytest tests/unit_tests/        # Only unit tests
pytest tests/unit_tests/test_main.py  # Single test file
pytest -v                       # Verbose output
pytest --cov=src/atlas         # With coverage

# Code quality
ruff check src/                 # Linting
ruff format src/                # Auto-format
pyright src/                    # Type checking
bandit -r src/                  # Security scan
pip-audit                       # Dependency audit

# Run the CLI
python -m atlas                 # Via module
atlas                          # If installed

# Build & distribute
python -m build                 # Create wheel/sdist
```

### Pre-commit Hooks

The project uses pre-commit. Install hooks:
```bash
pre-commit install
pre-commit run --all-files      # Run manually
```

## Architecture Notes

### src/atlas Package

**Purpose**: Programmatic interface to Atlas browser for red teaming.

**Core Modules**:

1. **api.py** - OpenAI Client wrapper
   - `client`: Global Client instance using `OPEN_AI_API_KEY_RED_TEAM` env var
   - `get_conversation()`: Retrieve conversation objects from API
   - Low-level API interaction

2. **constants.py** - Platform-specific paths
   - `ATLAS_APP_EXECUTABLE_PATH`: Path to ChatGPT Atlas.app (macOS)
   - `ATLAS_CACHE_FOLDER`, `ATLAS_CONFIG_FOLDER`: App data locations
   - User cache/config/log folders via platformdirs

3. **interact.py** - GUI automation
   - `sync_atlas_browser()`: Context manager launching Playwright browser context
   - `run_conversation()`: Execute planned conversation with Atlas GUI
   - Uses keyboard/mouse control via pynput
   - Supports Playwright tracing for debugging

4. **demo.py** - Conversation management utilities
   - `save_planned_conversation()`: Serialize to JSON with validation
   - `load_planned_conversation()`: Deserialize from JSON
   - `transfer_raw_copied_to_planned_conversation()`: Parse clipboard text to conversation
   - Works with OpenAI's `ItemCreateParams` structures

5. **parse.py** - Data parsing
   - Parse raw conversation text into structured Message objects
   - Handles multi-turn conversation formatting

6. **process.py** - Process management
   - `get_atlas_process()`: Find running Atlas by process name
   - Uses psutil for cross-platform process queries

7. **_typing.py** - Type definitions
   - `PlannedConversation`: Pydantic model validating conversation structure
   - Reusable type hints across modules

**Data Flow**:
1. Load/create conversation via `demo.py`
2. Launch browser via `interact.py`
3. Run conversation, capturing interactions
4. Parse results via `parse.py`
5. Save to structured format with validation

### joestuff/red_teaming [Legacy]

This is a complete PyRIT-based red teaming framework (separate documentation in joestuff/red_teaming/ARCHITECTURE.md). Key difference from src/atlas:
- Uses PyRIT framework abstractions
- API-based testing (not GUI automation)
- Automated scoring and reporting
- Multiple attack strategy categories

### Testing Architecture

- **unit_tests/**: Test __main__ CLI command
- **integration_tests/**: (Currently empty, planned for API integration tests)
- **acceptance_tests/**: (Currently empty, planned for full system tests)
- **conftest.py**: Shared pytest fixtures
- Tests importable as `from atlas import __main__`

### Configuration & Secrets

- **Environment Variables** (required):
  - `OPEN_AI_API_KEY_RED_TEAM`: OpenAI API key for conversations API
  - `ATLAS_APP_EXECUTABLE_PATH`: Can override in constants.py

- **Dev Dependencies** (pyproject.toml):
  - Split into `dev` group
  - Includes pytest, pyright, ruff, commitizen

## Key Design Decisions

1. **Pydantic Validation**: Conversation structures validated via `PlannedConversation` model
2. **Context Managers**: Browser sessions use `sync_atlas_browser()` for proper cleanup
3. **Cross-platform**: Uses platformdirs for OS-appropriate paths
4. **Logging**: Integrated with loguru for structured logs
5. **CLI-first**: Typer provides clean command-line interface
6. **Type Safety**: Pyright for static analysis, type hints throughout

## Development Patterns

### Adding New Commands

```python
# In __main__.py
from typer import Typer

app = Typer()

@app.command()
def my_command(arg: str) -> None:
    """Do something with Atlas."""
    # Implementation
```

### Working with Conversations

```python
# Load planned conversation
from atlas.demo import load_planned_conversation
from pathlib import Path

params = load_planned_conversation(Path("data/conversation.json"))

# Run via browser
from atlas.interact import sync_atlas_browser
with sync_atlas_browser() as browser:
    # Automation code here
    pass
```

### Adding Tests

```bash
# Unit tests: src/atlas module behavior
pytest tests/unit_tests/test_*.py -v

# Integration tests: API + module interaction
pytest tests/integration_tests/ -v

# Acceptance tests: Full system behavior
pytest tests/acceptance_tests/ -v
```

## Terraform Infrastructure

The `terraform/` directory provisions an AWS Mac2 instance for running Atlas. See `terraform/` for deployment details. Note: This is separate from the Python package in `src/atlas`.

## Known Limitations & TODOs

1. **agent.py**: Currently empty stub (pending implementation)
2. **Integration tests**: Empty - need API integration tests
3. **Acceptance tests**: Empty - need full system tests
4. **interact.py**: Incomplete `run_conversation()` and `enter_prompt()` implementations
5. **Multi-platform support**: Some paths hardcoded for macOS (ATLAS_APP_EXECUTABLE_PATH)

## Debugging Tips

- **Process not found**: Ensure Atlas application is running: `ps aux | grep Atlas`
- **API errors**: Check `OPEN_AI_API_KEY_RED_TEAM` environment variable is set
- **Playwright issues**: Check browser executable path, may differ on your system
- **Tracing**: Use `context.tracing` in interact.py to record browser interactions for debugging
