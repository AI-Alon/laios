# Creating Plugins

Plugins extend LAIOS without modifying core code. They can register new tools, intercept task parameters, react to lifecycle events, and modify messages.

**Prerequisites:** Familiarity with [Plugins API Reference](../api/plugins.md).

---

## What Plugins Can Do

| Capability | How |
|-----------|-----|
| Add new tools | `context.tool_registry.register_tool(MyTool)` in `on_load()` |
| Subscribe to events | `context.event_bus.subscribe("task.*", handler)` |
| Intercept task parameters | Override `on_before_task()` and return modified dict |
| Intercept messages | Override `on_message()` and return modified content |
| React to task completion | Override `on_after_task()` for logging/alerting |
| React to session lifecycle | Override `on_session_start()`, `on_session_end()` |

---

## Plugin Discovery

Place your plugin in the standard directory:

```
~/.laios/plugins/
└── my_plugin/
    ├── plugin.py     ← required: contains PluginBase subclass
    └── helpers.py    ← optional: any other Python files
```

Alternatively, add a custom directory to `config/default.yaml`:

```yaml
plugins:
  enabled: true
  directories:
    - "~/.laios/plugins"
    - "./my_project/plugins"   # ← add your directory here
```

---

## Minimal Plugin

```python
# ~/.laios/plugins/hello_plugin/plugin.py
from laios.plugins.base import PluginBase, PluginContext

class HelloPlugin(PluginBase):
    name = "hello_plugin"
    version = "1.0.0"
    description = "Greets every session"
    author = "your-name"
    tags = ["demo"]

    def on_load(self, context: PluginContext) -> None:
        print(f"HelloPlugin loaded. LLM model: {context.config.llm.model}")

    def on_session_start(self, session_id: str, user_id: str) -> None:
        print(f"Hello {user_id}! Session {session_id[:8]}... started.")
```

**Verify discovery:**

```bash
laios plugins list
# → hello_plugin  1.0.0  Greets every session  [enabled]
```

---

## Registering Tools from a Plugin

The most common plugin use case:

```python
from laios.plugins.base import PluginBase, PluginContext
from laios.tools.base import BaseTool, ToolCategory, ToolInput
from pydantic import Field

class SentimentInput(ToolInput):
    text: str = Field(description="Text to analyze")

class SentimentTool(BaseTool):
    name = "nlp.sentiment"
    description = "Basic positive/negative/neutral sentiment analysis"
    category = ToolCategory.DATA
    input_model = SentimentInput

    def _execute(self, input_data: SentimentInput):
        positive = {"good", "great", "excellent", "love"}
        negative = {"bad", "terrible", "hate", "awful"}
        words = set(input_data.text.lower().split())
        pos = len(words & positive)
        neg = len(words & negative)
        sentiment = "positive" if pos > neg else "negative" if neg > pos else "neutral"
        return {"sentiment": sentiment}


class NLPPlugin(PluginBase):
    name = "nlp_plugin"
    version = "1.0.0"
    description = "Adds NLP tools"

    def on_load(self, context: PluginContext) -> None:
        context.tool_registry.register_tool(SentimentTool)
        print("NLPPlugin: registered nlp.sentiment")

    def on_unload(self) -> None:
        print("NLPPlugin: unloaded")
```

After loading, the tool is available:

```bash
laios tools describe nlp.sentiment
laios tools run nlp.sentiment --params '{"text": "This is great!"}'
```

---

## Subscribing to Events

```python
from laios.plugins.base import PluginBase, PluginContext
from typing import Any, Dict

class MonitorPlugin(PluginBase):
    name = "monitor_plugin"
    version = "1.0.0"
    description = "Logs all task events to a file"

    def on_load(self, context: PluginContext) -> None:
        # Subscribe to all task events (wildcard)
        context.event_bus.subscribe("task.*", self._on_task_event)
        # Subscribe to plan events
        context.event_bus.subscribe("plan.created", self._on_plan_created)

    def _on_task_event(self, event_name: str, data: Dict[str, Any]) -> None:
        task_id = data.get("task_id", "?")[:8]
        tool = data.get("tool", "?")
        print(f"[Monitor] {event_name}: task={task_id}, tool={tool}")

    def _on_plan_created(self, event_name: str, data: Dict[str, Any]) -> None:
        plan_id = data.get("plan_id", "?")[:8]
        task_count = data.get("task_count", 0)
        print(f"[Monitor] Plan {plan_id} created with {task_count} tasks")
```

**Available wildcard patterns:**

| Pattern | Matches |
|---------|---------|
| `"task.*"` | `task.started`, `task.completed`, `task.failed` |
| `"session.*"` | `session.started`, `session.ended` |
| `"*"` | All events |
| `"plan.created"` | Exact match only |

---

## Intercepting Task Parameters (`on_before_task`)

Override `on_before_task` to modify or audit tool invocations:

```python
from typing import Any, Dict, Optional

class SafetyPlugin(PluginBase):
    name = "safety_plugin"
    version = "1.0.0"
    description = "Adds safety guardrails for shell commands"

    def on_before_task(
        self,
        task_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if tool_name == "shell.execute":
            command = parameters.get("command", "")

            # Block dangerous commands
            if "rm -rf" in command:
                raise ValueError("rm -rf is not permitted by SafetyPlugin")

            # Enforce a timeout if not set
            if "timeout" not in parameters:
                parameters["timeout"] = 30
                return parameters

        return None  # Return None to leave other tools unmodified
```

**Key rules:**
- Return a `dict` to replace the parameters (the next plugin receives your modified dict)
- Return `None` to pass the original parameters unchanged
- Raise an exception to abort the task entirely — the executor will catch it and create a failed `TaskResult`

---

## Intercepting Messages (`on_message`)

```python
class ContentFilterPlugin(PluginBase):
    name = "content_filter"
    version = "1.0.0"
    description = "Filters prohibited words from messages"

    BANNED = {"confidential", "secret"}

    def on_message(self, session_id: str, role: str, content: str) -> Optional[str]:
        modified = content
        for word in self.BANNED:
            modified = modified.replace(word, "[REDACTED]")
        # Return None if unchanged (more efficient than returning same string)
        return modified if modified != content else None
```

---

## Declaring Dependencies

If your plugin requires another plugin to be loaded first:

```python
class AdvancedPlugin(PluginBase):
    name = "advanced_plugin"
    version = "1.0.0"
    description = "Depends on nlp_plugin"
    dependencies = ["nlp_plugin"]   # ← must be loaded before this plugin
```

The `PluginLoader` performs topological sort. If a dependency is missing, `PluginDependencyError` is raised and neither plugin loads.

---

## Plugin Management CLI

```bash
# List all plugins with status
laios plugins list

# Disable a plugin (keeps it in memory, skips hooks)
laios plugins disable my_plugin

# Re-enable it
laios plugins enable my_plugin
```

---

## Testing Plugins

You can test plugins without running a full `AgentController`:

```python
import pytest
from laios.plugins.base import PluginContext
from laios.plugins.events import EventBus
from laios.tools.registry import ToolRegistry
from laios.core.types import Config


def make_context():
    return PluginContext(
        tool_registry=ToolRegistry(),
        config=Config(),
        event_bus=EventBus(),
    )


def test_nlp_plugin_registers_tool():
    context = make_context()
    plugin = NLPPlugin()
    plugin.on_load(context)

    assert context.tool_registry.has_tool("nlp.sentiment")


def test_sentiment_tool_positive():
    tool = SentimentTool()
    result = tool.execute(text="This is great and excellent!")
    assert result.success
    assert result.data["sentiment"] == "positive"


def test_safety_plugin_blocks_rm_rf():
    plugin = SafetyPlugin()
    with pytest.raises(ValueError, match="rm -rf"):
        plugin.on_before_task(
            task_id="t1",
            tool_name="shell.execute",
            parameters={"command": "rm -rf /tmp/test"},
        )
```

---

## Best Practices

1. **Keep `on_load` fast** — avoid network calls or heavy initialization; they block agent startup.
2. **Handle exceptions** — if your event handler or hook raises, it is caught and logged, but other plugins are unaffected.
3. **Be idempotent in `on_before_task`** — the hook may be called multiple times if the agent replans.
4. **Use tags** — `tags = ["monitoring", "security"]` helps operators discover and organize plugins.
5. **Version semantically** — increment the minor version when you add new hooks or tools; major version for breaking changes.
6. **Clean up in `on_unload`** — close file handles, database connections, and cancel background threads.
