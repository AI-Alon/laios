# LAIOS — Local AI Operating System

**LAIOS** is a local-first, privacy-preserving autonomous agent framework for Python. It gives you a production-ready AI agent that plans, executes, reflects, and remembers — all running on your machine with no data sent to the cloud by default.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Autonomous execution** | Converts natural-language goals into multi-step plans and executes them |
| **Three-tier memory** | Short-term (session), long-term (persistent), and episodic (per-goal) memory |
| **Extensible tools** | 15 built-in tools; add your own in < 20 lines |
| **Plugin system** | Lifecycle hooks, event bus, hot-enable/disable — no restart needed |
| **Multi-provider LLM** | Ollama, OpenAI, Anthropic; fallback and round-robin routing |
| **Trust levels** | PARANOID (plan only) → BALANCED (safe ops) → AUTONOMOUS (unattended) |
| **Web UI & REST API** | Optional FastAPI server + browser interface |
| **Streaming chat** | Token-by-token output via `process_message_stream()` |

---

## Choose Your Path

| I want to… | Start here |
|------------|------------|
| Get up and running in 5 minutes | [Quick Start](quickstart.md) |
| Understand how LAIOS works | [Architecture](architecture.md) |
| Follow step-by-step tutorials | [Tutorial 1: Your First Agent](tutorials/01-first-agent.md) |
| Add a custom tool | [Guide: Creating Tools](guides/creating-tools.md) |
| Write a plugin | [Guide: Creating Plugins](guides/creating-plugins.md) |
| Browse runnable examples | [Examples](../examples/README.md) |
| Look up a class or method | [API Reference](api/index.md) |
| See what's planned | [Roadmap](ROADMAP.md) |

---

## Quick Example

```python
from laios import Config, Goal
from laios.core.agent import AgentController

agent = AgentController(Config())
session = agent.create_session(user_id="alice")

# Chat
print(agent.process_message(session.id, "What tools do you have?"))

# Execute a structured goal
result = agent.execute_goal(session.id, Goal(
    description="List all Python files in the current directory"
))
print(f"Success: {result['success']}, tasks run: {len(result['results'])}")

agent.shutdown_session(session.id)
```

---

## Installation

```bash
git clone https://github.com/AI-Alon/laios.git
cd laios/LAIOS
pip install -e ".[dev,llm]"

# Pull a local model
ollama pull llama2

# Verify
laios info
```

---

## Community

- **Issues & bug reports:** [GitHub Issues](https://github.com/AI-Alon/laios/issues)
- **Discussions & questions:** [GitHub Discussions](https://github.com/AI-Alon/laios/discussions)
- **License:** MIT
