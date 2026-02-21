# Frequently Asked Questions

---

## Setup & Installation

### Q: What Python version does LAIOS require?

Python 3.10 or later. Python 3.11+ is recommended for best performance and compatibility with the latest Pydantic v2 features.

---

### Q: Do I need a GPU to run LAIOS?

No. Ollama handles LLM inference and can run on CPU, though responses will be slower. For GPU acceleration, Ollama automatically uses available CUDA or Metal hardware.

---

### Q: How do I fix `laios: command not found`?

Run `pip install -e .` from the `LAIOS/` directory, then verify with `laios info`. If using a virtual environment, make sure it is activated before installing.

---

### Q: Can I use LAIOS without Ollama?

Yes. Configure an OpenAI or Anthropic key in a `.env` file and set `llm.provider` in your config to `"openai"` or `"anthropic"`. See [Quick Start — Cloud LLM Providers](quickstart.md#cloud-llm-providers).

---

### Q: How do I switch between models?

Edit your config YAML or pass `Config(llm=LLMConfig(model="gemma3:4b"))` in Python. CLI: `laios chat --config my_config.yaml`.

---

## Tools

### Q: How many built-in tools does LAIOS have?

15 tools across six categories: filesystem, system, web, data, code, and search. Run `laios tools list` to see them all.

---

### Q: Can I add my own tools?

Yes. Subclass `BaseTool`, define `_execute()`, and call `registry.register_tool(MyTool)`. See [Guide: Creating Tools](guides/creating-tools.md) for a full walkthrough.

---

### Q: Can tools run asynchronously?

Yes. Subclass `AsyncBaseTool` instead of `BaseTool` and implement `_execute()` as a coroutine. The `Executor` handles scheduling via `asyncio`.

---

### Q: How does the agent know which tools to use?

`ToolRegistry.get_schema_for_llm()` returns all tool schemas in a format the LLM understands. The `Planner` passes these to the LLM during plan creation so it can select the right tool for each task.

---

## Plugins

### Q: Where should I place my plugin files?

Create a directory at `~/.laios/plugins/<plugin_name>/plugin.py`. The plugin system discovers all subdirectories in configured plugin directories on startup. See [Guide: Creating Plugins](guides/creating-plugins.md).

---

### Q: Can I disable a plugin without restarting?

Yes. `laios plugins disable <name>` skips all hooks for that plugin without unloading it. Re-enable with `laios plugins enable <name>`. In Python use `registry.disable_plugin(name)` / `registry.enable_plugin(name)`.

---

### Q: Can `on_before_task()` modify tool parameters?

Yes. Return a modified dict from `on_before_task()` and the executor will use your dict instead of the original. Return `None` to leave parameters unchanged. Multiple plugins chain: each receives the output of the previous.

---

## Memory

### Q: Where is memory stored on disk?

By default in `~/.laios/memory/`. Long-term memories go to `long_term.json` and episodic memories to `episodes/<episode_id>.json`. The path is configurable via `memory.storage_path` in your config.

---

### Q: How do I clear all stored memory?

```bash
rm -rf ~/.laios/memory/
```

Or in Python: retrieve the `MemoryStore` via `agent.get_memory()` and call the relevant delete methods. Be careful — this is permanent.

---

### Q: Is memory searched on every chat message?

No. Memory search runs only on the first message of a session to seed context. Subsequent messages in the same session use the established conversation history without repeating the memory lookup.

---

## Security & Privacy

### Q: Does LAIOS send my data to any external server?

Only if you configure an external LLM provider (OpenAI, Anthropic). With Ollama, all inference is local. No telemetry or usage data is collected.

---

### Q: What is the `paranoid` trust level?

`PARANOID` makes the agent plan the tasks but **not** execute them. The returned dict contains `"awaiting_approval": True` and the plan. You can inspect it and call `agent.approve_and_execute(session.id, plan)` to proceed. Use this when you want human review before any actions are taken.
