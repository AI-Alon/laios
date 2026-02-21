# Quick Start Guide

## Installation

### 1. Install Python Dependencies

```bash
cd LAIOS
pip install -e ".[dev,llm]"
```

### 2. Install Ollama (for local LLM)

Visit [https://ollama.ai/download](https://ollama.ai/download) or:

```bash
# macOS/Linux
curl https://ollama.ai/install.sh | sh

# Verify installation
ollama --version
```

### 3. Pull an LLM Model

```bash
ollama pull llama2
# or for a smaller, faster model
ollama pull gemma3:4b
```

## Basic Usage

### Interactive Chat

```bash
laios chat
```

Type `exit`, `quit`, or `bye` to end the session. Sessions are automatically saved to `~/.laios/sessions/`.

### Execute a Goal

```bash
laios run "find all Python files and list them"
laios run "analyze this directory and create a summary"
```

### Check System Status

```bash
laios info
```

## Configuration

Create a custom config file:

```yaml
# my_config.yaml
llm:
  provider: "ollama"
  model: "llama2"
  temperature: 0.7

agent:
  trust_level: "balanced"
```

Use it:

```bash
laios chat --config my_config.yaml
```

**Trust levels:**

| Level | Behavior |
|-------|----------|
| `paranoid` | Shows plan but does not execute — requires manual approval |
| `balanced` | Auto-executes safe operations (default) |
| `autonomous` | Auto-executes everything without confirmation |

## Programmatic Usage

```python
from laios import Config, Goal
from laios.core.agent import AgentController

# Initialize with default config (ollama/llama2)
config = Config()
agent = AgentController(config)

# Create session
session = agent.create_session(user_id="your_user_id")

# Chat
response = agent.process_message(session.id, "What tools do you have?")
print(response)

# Streaming chat
for chunk in agent.process_message_stream(session.id, "Tell me a story"):
    print(chunk, end="", flush=True)

# Execute structured goal
goal = Goal(description="List all Python files in the current directory")
result = agent.execute_goal(session.id, goal)
print(f"Success: {result['success']}")
print(f"Tasks run: {len(result['results'])}")

# Clean up
agent.shutdown_session(session.id)
```

## Cloud LLM Providers

To use OpenAI or Anthropic instead of Ollama, add keys to a `.env` file:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

Then configure in your YAML:

```yaml
llm:
  provider: "openai"     # or "anthropic"
  model: "gpt-4o"        # or "claude-sonnet-4-6"
```

## Tool Management

```bash
# List all available tools
laios tools list

# List tools by category
laios tools list --category filesystem

# Get detailed info about a tool
laios tools describe filesystem.read_file

# Run a tool directly
laios tools run filesystem.read_file --params '{"path": "README.md"}'
```

## Memory

```bash
# Search memories
laios memory search "python best practices"

# List recent memories
laios memory list --type long_term
laios memory list --type episodic
```

## Session Management

```bash
# List saved sessions
laios sessions list

# Resume a session
laios sessions resume <session-id-prefix>

# Delete a session
laios sessions delete <session-id>
```

## Web UI

```bash
# Start the API server and web interface
laios serve --host 0.0.0.0 --port 8000
# Open http://localhost:8000 in your browser
```

Requires: `pip install -e ".[api]"`

## Development

```bash
# Run tests
pytest

# With coverage
pytest --cov=laios --cov-report=html
open htmlcov/index.html

# Format code
black laios tests

# Lint
ruff laios tests

# Type check
mypy laios
```

## Troubleshooting

### "laios command not found"

```bash
pip install -e .
```

### Ollama connection errors

```bash
# Start the Ollama server
ollama serve

# In another terminal, verify it's running
ollama list
```

### LLM initialization errors

Make sure the model is pulled:

```bash
ollama pull llama2
```

### Import errors

```bash
pip install -e ".[dev,llm]"
```

## Next Steps

- **[Tutorials](tutorials/01-first-agent.md)** — step-by-step guides
- **[Developer Guides](guides/creating-tools.md)** — extend LAIOS with custom tools and plugins
- **[API Reference](api/index.md)** — complete API documentation
- **[Examples](../examples/README.md)** — runnable example scripts
- **[Architecture](architecture.md)** — system design documentation

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/AI-Alon/laios/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AI-Alon/laios/discussions)
