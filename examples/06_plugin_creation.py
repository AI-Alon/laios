"""
Example 06: Programmatic Plugin Creation
==========================================
Demonstrates:
  - Defining NLPPlugin with SentimentTool entirely in Python (no filesystem)
  - PluginRegistry.register(), list_plugins(), disable_plugin()
  - EventBus wildcard subscription to react to task events
  - on_before_task() parameter normalization
  - Direct event bus emit to show plugin reaction

Requirements:
  - No LLM required — runs fully offline

Run:
  python examples/06_plugin_creation.py
"""

from typing import Any, Dict

from pydantic import Field

from laios.plugins.base import PluginBase, PluginContext
from laios.plugins.events import EventBus, get_event_bus
from laios.plugins.registry import PluginRegistry
from laios.tools.base import BaseTool, ToolCategory, ToolInput


# ── SentimentTool ─────────────────────────────────────────────────────────────

class SentimentInput(ToolInput):
    text: str = Field(description="Text to analyse for sentiment")


class SentimentTool(BaseTool):
    """Rule-based sentiment tool — no ML required."""

    name = "nlp.sentiment"
    description = "Classify text sentiment as positive, negative, or neutral"
    category = ToolCategory.DATA
    input_model = SentimentInput
    required_permissions = set()

    _POSITIVE = {"great", "good", "excellent", "wonderful", "happy", "love", "amazing", "fantastic"}
    _NEGATIVE = {"bad", "terrible", "awful", "horrible", "hate", "poor", "dreadful", "worst"}

    def _execute(self, input_data: SentimentInput) -> dict:
        words = set(input_data.text.lower().split())
        pos = len(words & self._POSITIVE)
        neg = len(words & self._NEGATIVE)
        if pos > neg:
            label, score = "positive", round(pos / max(len(words), 1), 3)
        elif neg > pos:
            label, score = "negative", round(-neg / max(len(words), 1), 3)
        else:
            label, score = "neutral", 0.0
        return {"label": label, "score": score, "word_count": len(words)}


# ── NLPPlugin ─────────────────────────────────────────────────────────────────

class NLPPlugin(PluginBase):
    name = "nlp"
    version = "1.0.0"
    description = "Adds NLP tools and normalises text parameters before execution"
    author = "example"
    tags = ["nlp", "tools", "example"]

    def on_load(self, context: PluginContext) -> None:
        # Register tool
        context.tool_registry.register_tool(SentimentTool)

        # Subscribe to ALL task events via wildcard
        context.event_bus.subscribe("task.*", self._on_task_event)

        self._events_received: list[str] = []
        print("[NLPPlugin] Loaded — SentimentTool registered, wildcard subscription active")

    def on_unload(self) -> None:
        print(f"[NLPPlugin] Unloaded — saw {len(self._events_received)} task event(s)")

    def on_session_start(self, session_id: str, user_id: str) -> None:
        print(f"[NLPPlugin] Session started: user={user_id}, id={session_id[:8]}...")

    def on_before_task(
        self,
        task_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any] | None:
        """Strip leading/trailing whitespace from any 'text' parameter."""
        if "text" in parameters:
            original = parameters["text"]
            cleaned = original.strip()
            if cleaned != original:
                print(f"[NLPPlugin] on_before_task: stripped whitespace from 'text'")
                return {**parameters, "text": cleaned}
        return None  # no change

    def on_after_task(
        self,
        task_id: str,
        tool_name: str,
        success: bool,
        result: Any,
    ) -> None:
        status = "OK" if success else "FAIL"
        print(f"[NLPPlugin] Task {task_id[:8]} [{status}] via {tool_name}")

    def _on_task_event(self, event_name: str, data: Dict[str, Any]) -> None:
        self._events_received.append(event_name)
        task_id = data.get("task_id", "?")[:8]
        print(f"[NLPPlugin] Event: {event_name} (task={task_id})")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== Plugin Creation Example ===\n")

    # ── Setup: shared EventBus and PluginRegistry ──
    event_bus = get_event_bus()
    registry = PluginRegistry()

    # Build a minimal PluginContext pointing at a fresh ToolRegistry
    from laios.tools.registry import ToolRegistry
    tool_registry = ToolRegistry()

    context = PluginContext(
        tool_registry=tool_registry,
        event_bus=event_bus,
    )

    # ── Register the plugin ──
    print("--- Registering NLPPlugin ---")
    registry.register(NLPPlugin, context)

    # ── List plugins ──
    print("\n--- Loaded Plugins ---")
    for meta in registry.list_plugins():
        print(f"  {meta.name} v{meta.version}  enabled={meta.enabled}  tags={meta.tags}")

    # ── Run SentimentTool directly ──
    print("\n--- SentimentTool: positive text ---")
    result = tool_registry.execute_tool("nlp.sentiment", text="This is a great and wonderful day!")
    if result.success:
        print(f"  label={result.data['label']}, score={result.data['score']}, words={result.data['word_count']}")

    print("\n--- SentimentTool: negative text ---")
    result = tool_registry.execute_tool("nlp.sentiment", text="That was a terrible and awful experience.")
    if result.success:
        print(f"  label={result.data['label']}, score={result.data['score']}")

    print("\n--- SentimentTool: neutral text ---")
    result = tool_registry.execute_tool("nlp.sentiment", text="The package arrived on Tuesday.")
    if result.success:
        print(f"  label={result.data['label']}, score={result.data['score']}")

    # ── Demonstrate on_before_task via direct hook dispatch ──
    print("\n--- on_before_task: whitespace normalization ---")
    modified = registry.dispatch_before_task(
        task_id="test-task-0001",
        tool_name="nlp.sentiment",
        parameters={"text": "  extra whitespace  "},
    )
    print(f"  original : '  extra whitespace  '")
    print(f"  modified : '{modified.get('text', '(unchanged)')}'")

    # ── Emit a task event to trigger wildcard subscription ──
    print("\n--- EventBus emit: task.started ──")
    event_bus.emit("task.started", {"task_id": "demo-task-abcd", "tool": "nlp.sentiment"})

    print("\n--- EventBus emit: task.completed ---")
    event_bus.emit("task.completed", {"task_id": "demo-task-abcd", "tool": "nlp.sentiment"})

    # ── Disable plugin ──
    print("\n--- Disabling NLPPlugin ---")
    registry.disable_plugin("nlp")
    for meta in registry.list_plugins():
        print(f"  {meta.name}  enabled={meta.enabled}")

    # ── Hooks should be silent when disabled ──
    print("\n--- Emit after disable (no plugin output expected) ---")
    event_bus.emit("task.started", {"task_id": "demo-task-efgh", "tool": "nlp.sentiment"})
    print("  (no [NLPPlugin] output above = correct)")

    # ── Re-enable ──
    print("\n--- Re-enabling NLPPlugin ---")
    registry.enable_plugin("nlp")
    for meta in registry.list_plugins():
        print(f"  {meta.name}  enabled={meta.enabled}")

    # ── Unload ──
    print("\n--- Unloading all plugins ---")
    registry.unload_all()

    print("\nDone.")


if __name__ == "__main__":
    main()
