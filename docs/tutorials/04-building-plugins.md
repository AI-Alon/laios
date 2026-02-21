# Tutorial 4: Building Your First Plugin

In this tutorial you will write a plugin from scratch, deploy it to the standard plugin directory, and verify it is discovered and running via the CLI.

**Time:** ~20 minutes
**Difficulty:** Intermediate
**Prerequisite:** [Tutorial 1: Your First Agent](01-first-agent.md), [Guide: Creating Plugins](../guides/creating-plugins.md)

---

## What You'll Build

A plugin called `word_counter` that:

1. Registers a `text.word_count` tool
2. Logs every task completion to a file (`~/word_counter_events.txt`)
3. Greets users on session start

---

## Step 1: Create the Plugin Directory

```bash
mkdir -p ~/.laios/plugins/word_counter
```

---

## Step 2: Write `plugin.py`

Create `~/.laios/plugins/word_counter/plugin.py` with the following content:

```python
"""
Word Counter Plugin

Registers a word-count tool and logs all task events to a file.
"""

import pathlib
from typing import Any, Dict, Optional

from pydantic import Field

from laios.plugins.base import PluginBase, PluginContext
from laios.tools.base import BaseTool, ToolCategory, ToolInput


# ── Tool Definition ──────────────────────────────────────────────────────────

class WordCountInput(ToolInput):
    text: str = Field(description="Text to count words in")


class WordCountTool(BaseTool):
    name = "text.word_count"
    description = "Count the number of words in a piece of text"
    category = ToolCategory.DATA
    input_model = WordCountInput
    required_permissions = set()

    def _execute(self, input_data: WordCountInput):
        words = input_data.text.split()
        return {
            "word_count": len(words),
            "char_count": len(input_data.text),
            "unique_words": len(set(w.lower() for w in words)),
        }


# ── Plugin Definition ─────────────────────────────────────────────────────────

class WordCounterPlugin(PluginBase):
    name = "word_counter"
    version = "1.0.0"
    description = "Adds word-count tool and logs task events"
    author = "tutorial"
    tags = ["tools", "monitoring", "tutorial"]

    def on_load(self, context: PluginContext) -> None:
        # Register the tool
        context.tool_registry.register_tool(WordCountTool)

        # Subscribe to task events
        context.event_bus.subscribe("task.*", self._log_task_event)

        # Set up log file
        self._log_path = pathlib.Path("~/word_counter_events.txt").expanduser()
        self._log("Plugin loaded")
        print(f"[WordCounter] Loaded. Log file: {self._log_path}")

    def on_unload(self) -> None:
        self._log("Plugin unloaded")
        print("[WordCounter] Unloaded.")

    def on_session_start(self, session_id: str, user_id: str) -> None:
        print(f"[WordCounter] Hello {user_id}! Session {session_id[:8]}... started.")
        self._log(f"Session started: user={user_id}, session={session_id[:8]}")

    def on_session_end(self, session_id: str) -> None:
        self._log(f"Session ended: session={session_id[:8]}")

    def on_after_task(self, task_id: str, tool_name: str, success: bool, result: Any) -> None:
        status = "OK" if success else "FAIL"
        print(f"[WordCounter] Task {task_id[:8]} [{status}]: {tool_name}")

    def _log_task_event(self, event_name: str, data: Dict[str, Any]) -> None:
        task_id = data.get("task_id", "?")[:8]
        tool = data.get("tool", "?")
        self._log(f"{event_name}: task={task_id}, tool={tool}")

    def _log(self, message: str) -> None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self._log_path, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
```

---

## Step 3: Verify Plugin Discovery

```bash
laios plugins list
```

Expected output:

```
Plugins (1 loaded):
─────────────────────────────────────────
Name:        word_counter
Version:     1.0.0
Description: Adds word-count tool and logs task events
Author:      tutorial
Tags:        tools, monitoring, tutorial
Enabled:     yes
```

If the plugin does not appear, check that:

1. The file is at `~/.laios/plugins/word_counter/plugin.py`
2. The class `WordCounterPlugin` inherits from `PluginBase`
3. `name`, `version`, and `description` are set

---

## Step 4: Use the New Tool via CLI

```bash
# Inspect the tool schema
laios tools describe text.word_count
```

Expected output:

```
Tool: text.word_count
Description: Count the number of words in a piece of text
Category: data
Parameters:
  text (string, required): Text to count words in
Permissions: none
```

```bash
# Run the tool directly
laios tools run text.word_count --params '{"text": "Hello world, this is LAIOS!"}'
```

Expected output:

```json
{
  "success": true,
  "data": {
    "word_count": 5,
    "char_count": 27,
    "unique_words": 5
  }
}
```

---

## Step 5: Use the Tool from Python

```python
from laios.core.agent import AgentController
from laios.core.types import Config

agent = AgentController(Config())  # WordCounterPlugin loads automatically
session = agent.create_session(user_id="tutorial_user")

# Execute the word count tool via the registry
registry = agent.get_tool_registry()
result = registry.execute_tool("text.word_count", text="The quick brown fox jumps over the lazy dog")

print(f"Word count: {result.data['word_count']}")    # 9
print(f"Unique words: {result.data['unique_words']}")  # 8
print(f"Characters: {result.data['char_count']}")     # 43

agent.shutdown_session(session.id)
```

---

## Step 6: Inspect the Event Log

```bash
cat ~/word_counter_events.txt
```

Expected output (timestamps will differ):

```
[2026-02-19 10:00:01] Plugin loaded
[2026-02-19 10:00:01] Session started: user=tutorial_user, session=abc12345
[2026-02-19 10:00:02] task.started: task=def56789, tool=text.word_count
[2026-02-19 10:00:02] task.completed: task=def56789, tool=text.word_count
[2026-02-19 10:00:02] Session ended: session=abc12345
[2026-02-19 10:00:02] Plugin unloaded
```

---

## Step 7: Disable and Re-enable

```bash
# Disable the plugin (keeps it in memory, skips all hooks)
laios plugins disable word_counter

# Verify
laios plugins list
# → word_counter ... Enabled: no

# Re-enable
laios plugins enable word_counter
```

---

## What You Built

| Feature | Code |
|---------|------|
| Custom tool | `WordCountTool` with `_execute()` |
| Tool registration | `context.tool_registry.register_tool(WordCountTool)` in `on_load()` |
| Event subscription | `context.event_bus.subscribe("task.*", self._log_task_event)` |
| Session hook | `on_session_start()` / `on_session_end()` |
| Task hook | `on_after_task()` |
| Plugin lifecycle | `on_load()` / `on_unload()` |

---

## Next Steps

- **[Guide: Creating Plugins](../guides/creating-plugins.md)** — parameter interception, message modification, dependency declaration
- **[Plugins API Reference](../api/plugins.md)** — complete lifecycle hook reference
- **[Example 06: Plugin Creation](../../examples/06_plugin_creation.py)** — programmatic plugin creation without the filesystem
