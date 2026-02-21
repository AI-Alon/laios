# Contributing to LAIOS

Thank you for your interest in contributing to LAIOS! This document provides guidelines for contributing to the project.

## Development Philosophy

LAIOS follows a strict engineering methodology:

1. **Architecture First** - Design before implementation
2. **Interface Stability** - APIs are contracts
3. **Test Coverage** - Every feature has tests
4. **Documentation** - Code is not done until documented

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- Ollama (for local LLM testing)

### Setup Steps

```bash
# Clone the repository
git clone https://github.com/AI-Alon/laios.git
cd laios

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev,api,llm]"

# Verify installation
laios version
pytest
```

## Code Standards

### Style Guide

- **Formatting**: Black (100 char line length)
- **Linting**: Ruff
- **Type Checking**: MyPy with strict mode
- **Docstrings**: Google style

### Before Committing

```bash
# Format code
black laios tests

# Lint
ruff laios tests

# Type check
mypy laios

# Run tests
pytest --cov=laios
```

## Contribution Workflow

### 1. Create an Issue

Before starting work, create an issue describing:
- What you want to build/fix
- Why it's needed
- Proposed approach

This allows discussion before implementation.

### 2. Fork and Branch

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/AI-Alon/laios.git
cd laios
git checkout -b feature/your-feature-name
```

### 3. Implement

Follow these guidelines:

- **Small PRs**: One feature/fix per PR
- **Tests First**: Write tests before implementation (TDD)
- **Documentation**: Update docs with code changes
- **Commit Messages**: Clear, descriptive messages

### 4. Test

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_planner.py

# Run with coverage
pytest --cov=laios --cov-report=html
```

### 5. Submit PR

- Write clear PR description
- Reference related issues
- Ensure CI passes
- Request review from maintainers

## Project Structure

Understanding the codebase:

```
laios/
├── core/           # Agent controller, types, config
├── reasoning/      # Intent parsing
├── planning/       # Task decomposition
├── execution/      # Tool invocation
├── tools/          # Tool registry and built-ins
├── memory/         # Memory systems
├── reflection/     # Self-evaluation
├── llm/            # LLM abstraction
└── ui/             # CLI and API
```

## Adding New Features

### Adding a New Tool

```python
# laios/tools/builtin/my_tool.py

from laios.core.types import Permission

def my_tool(param1: str) -> dict:
    """
    Brief description of what tool does.
    
    Args:
        param1: Description of parameter
    
    Returns:
        Dictionary with results
    """
    # Implementation
    return {"result": "..."}

# Register in laios/tools/builtin/__init__.py
from laios.tools.registry import ToolRegistry

def register_builtin_tools(registry: ToolRegistry):
    registry.register_tool(
        name="my_tool",
        description="Tool description",
        callable_func=my_tool,
        permissions={Permission.FILESYSTEM_READ}
    )
```

### Adding a New Subsystem

1. Create directory under `laios/`
2. Add `__init__.py`
3. Implement core classes
4. Write comprehensive tests
5. Update documentation
6. Integrate with `AgentController`

## Testing Guidelines

### Unit Tests

Test individual components in isolation:

```python
# tests/unit/test_planner.py

import pytest
from laios.planning import Planner
from laios.core.types import Goal

def test_planner_creates_valid_plan():
    planner = Planner()
    goal = Goal(description="Test goal")
    
    plan = planner.create_plan(goal, context=None)
    
    assert plan.goal == goal
    assert len(plan.tasks) >= 0
```

### Integration Tests

Test component interactions:

```python
# tests/integration/test_agent_flow.py

def test_full_agent_pipeline():
    agent = AgentController(config)
    session = agent.create_session("test_user")
    
    response = agent.process_message(
        session.id,
        "Create a file named test.txt"
    )
    
    assert "created" in response.lower()
```

### Fixtures

Reusable test data in `tests/fixtures/`:

```python
# tests/fixtures/goals.py

import pytest
from laios.core.types import Goal

@pytest.fixture
def simple_goal():
    return Goal(description="Simple test goal")
```

## Documentation

### Code Documentation

Every module, class, and function needs docstrings:

```python
def function_name(param1: str, param2: int) -> dict:
    """
    Brief one-line description.
    
    Longer description if needed, explaining behavior,
    edge cases, and design decisions.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When and why this is raised
    """
```

### User Documentation

- Update `README.md` for user-facing changes
- Add tutorials to `docs/tutorials/`
- Update architecture docs for structural changes

## Common Tasks

### Running the CLI

```bash
# Interactive chat
laios chat

# Execute single goal
laios run "your goal here"

# With custom config
laios chat --config my_config.yaml
```

### Debugging

```python
# Add to code
import structlog
logger = structlog.get_logger(__name__)

logger.debug("debug_info", key="value")
logger.info("info_message", data=some_data)
```

### Adding Dependencies

```bash
# Add to pyproject.toml under [project.dependencies]
# Then:
pip install -e ".[dev]"
```

## Release Process

(For maintainers)

1. Update version in `laios/__init__.py`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. GitHub Actions builds and publishes

## Getting Help

- **GitHub Discussions**: For questions and ideas
- **GitHub Issues**: For bugs and features
- **Discord**: For real-time chat (link in README)

## Code of Conduct

- Be respectful and inclusive
- Focus on technical merit
- Help others learn
- Assume good intentions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to LAIOS! 🚀
