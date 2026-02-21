# LAIOS Examples

Runnable Python scripts demonstrating the LAIOS API. Each script can be run with a single command.

## Quick Reference

| Script | What it Demonstrates | LLM Required | API Key Required |
|--------|----------------------|:------------:|:----------------:|
| [01_personal_assistant.py](01_personal_assistant.py) | Chat, long-term memory, streaming | Yes (Ollama) | No |
| [02_code_reviewer.py](02_code_reviewer.py) | `execute_goal()`, task results, episodes | Yes (Ollama) | No |
| [03_custom_tool.py](03_custom_tool.py) | `BaseTool`, `create_simple_tool`, ToolRegistry | No | No |
| [04_streaming.py](04_streaming.py) | `process_message_stream()`, latency comparison | Yes (Ollama) | No |
| [05_multi_provider_routing.py](05_multi_provider_routing.py) | `LLMRouter` fallback & round-robin | Yes (Ollama) | Optional (OpenAI) |
| [06_plugin_creation.py](06_plugin_creation.py) | `PluginBase`, `PluginRegistry`, `EventBus` | No | No |

## Prerequisites

```bash
# Install with LLM support (for examples requiring Ollama)
pip install -e ".[llm]"

# Start Ollama
ollama serve

# Pull a model (in another terminal)
ollama pull llama2
```

## Running Examples

```bash
# From the LAIOS root directory:
python examples/01_personal_assistant.py
python examples/02_code_reviewer.py README.md
python examples/03_custom_tool.py
python examples/04_streaming.py
python examples/05_multi_provider_routing.py
python examples/06_plugin_creation.py
```

## Example Descriptions

### 01 — Personal Assistant
Demonstrates multi-turn conversation with pre-seeded long-term memory. Shows how the agent uses stored context to give personalized responses from the first message.

### 02 — Code Reviewer
Uses `execute_goal()` with `AUTONOMOUS` trust level to analyze a file. Shows how to inspect `TaskResult` objects and retrieve the stored `Episode`.

### 03 — Custom Tool
Creates two tools — a class-based `HashTool` and a function-based `text.reverse` — then executes them directly via `ToolRegistry`. No LLM needed.

### 04 — Streaming
Side-by-side comparison of `process_message()` vs. `process_message_stream()`. Shows the time-to-first-token advantage of streaming.

### 05 — Multi-Provider Routing
Demonstrates `LLMRouter` with fallback and round-robin strategies. Shows how to inject a router into `AgentController` and track per-provider usage statistics.

### 06 — Plugin Creation
Creates a plugin programmatically (no filesystem) that registers a sentiment analysis tool, subscribes to all task events, and intercepts/normalizes task parameters. No LLM needed.
