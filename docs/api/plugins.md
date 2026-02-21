# Plugins API Reference

The `laios.plugins` package provides the plugin system: a base class with lifecycle hooks, a central registry, and a publish/subscribe event bus.

---

## PluginBase

**Import:** `from laios.plugins.base import PluginBase`

Abstract base class for all LAIOS plugins.

### Class Attributes (override in subclasses)

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | `"base_plugin"` | **Required.** Unique plugin identifier |
| `version` | `str` | `"0.1.0"` | **Required.** Plugin version (semantic versioning) |
| `description` | `str` | `"Base plugin"` | Human-readable description |
| `author` | `str` | `""` | Author name or email |
| `dependencies` | `List[str]` | `[]` | Names of plugins this plugin depends on |
| `tags` | `List[str]` | `[]` | Categorization tags (e.g., `["monitoring", "security"]`) |

### Constructor

```python
PluginBase()
```

Sets `_loaded = False`, `_enabled = True`, `_context = None`. Called automatically by `PluginLoader`.

---

### Required Methods

#### `on_load`

```python
@abstractmethod
on_load(context: PluginContext) -> None
```

Called when the plugin is loaded. Use this to register tools, subscribe to events, and initialize state.

**Parameters:** `context` — provides access to `tool_registry`, `config`, and `event_bus`.

```python
def on_load(self, context: PluginContext) -> None:
    context.tool_registry.register_tool(MyTool)
    context.event_bus.subscribe("task.*", self._on_task_event)
    self._config = context.config
```

---

#### `on_unload`

```python
on_unload(self) -> None
```

Called when the plugin is unregistered. Override to clean up resources (close connections, remove files, etc.).

Default implementation: does nothing.

---

### Lifecycle Hooks (override any)

All hooks are called by `PluginRegistry.dispatch_*()` on all enabled plugins. Exceptions raised in hooks are caught and logged — they do not propagate.

#### `on_session_start`

```python
on_session_start(session_id: str, user_id: str) -> None
```

Called when `AgentController.create_session()` creates a new session.

---

#### `on_session_end`

```python
on_session_end(session_id: str) -> None
```

Called when `AgentController.shutdown_session()` closes a session.

---

#### `on_before_task`

```python
on_before_task(
    task_id: str,
    tool_name: str,
    parameters: Dict[str, Any],
) -> Optional[Dict[str, Any]]
```

Called before each task is executed. Return a modified `parameters` dict to alter the tool invocation, or `None` to keep the original.

**Chaining:** Multiple plugins can modify parameters. Modifications chain — each plugin receives the output of the previous plugin's `on_before_task`.

```python
def on_before_task(self, task_id, tool_name, parameters):
    if tool_name == "shell.execute":
        # Inject --dry-run for all shell commands
        parameters["command"] = parameters["command"] + " --dry-run"
        return parameters
    return None  # pass through unmodified
```

---

#### `on_after_task`

```python
on_after_task(
    task_id: str,
    tool_name: str,
    success: bool,
    result: Any,
) -> None
```

Called after each task completes (success or failure). Use for logging, alerting, or metrics.

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | `str` | Task UUID |
| `tool_name` | `str` | Tool that was invoked |
| `success` | `bool` | Whether the task succeeded |
| `result` | `Any` | Tool output (on success) or error message (on failure) |

---

#### `on_before_plan`

```python
on_before_plan(goal_description: str) -> None
```

Called before the `Planner` creates a plan.

---

#### `on_after_plan`

```python
on_after_plan(plan_id: str, task_count: int) -> None
```

Called after the `Planner` creates a plan.

---

#### `on_message`

```python
on_message(
    session_id: str,
    role: str,
    content: str,
) -> Optional[str]
```

Called when a message is processed. Return a modified content string to alter the message, or `None` to keep the original.

**Chaining:** Like `on_before_task`, modifications chain through plugins.

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | `str` | Session UUID |
| `role` | `str` | `"user"` or `"assistant"` |
| `content` | `str` | Message text |

---

### State Properties

#### `enabled`

```python
@property
enabled -> bool

@enabled.setter
enabled(value: bool) -> None
```

Controls whether hooks are dispatched to this plugin. Disabled plugins remain registered but are skipped during hook dispatch.

---

### Info Methods

#### `get_info`

```python
get_info() -> Dict[str, Any]
```

Returns plugin metadata as a dictionary:

```python
{
    "name": "my_plugin",
    "version": "1.0.0",
    "description": "...",
    "author": "...",
    "loaded": True,
    "enabled": True,
    "dependencies": [],
    "tags": ["tools"],
}
```

---

#### `get_meta`

```python
get_meta() -> PluginMeta
```

Returns a `PluginMeta` object with the plugin's metadata.

---

## PluginContext

**Import:** `from laios.plugins.base import PluginContext`

Passed to `on_load()`. Provides access to core LAIOS systems.

### Constructor

```python
PluginContext(
    tool_registry: ToolRegistry,
    config: Config,
    event_bus: Optional[EventBus] = None,
)
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `tool_registry` | `ToolRegistry` | Register custom tools here |
| `config` | `Config` | Current LAIOS configuration |
| `event_bus` | `Optional[EventBus]` | Subscribe to and emit events |

---

## PluginMeta

**Import:** `from laios.plugins.base import PluginMeta`

Structured plugin metadata.

### Constructor

```python
PluginMeta(
    name: str,
    version: str,
    description: str = "",
    author: str = "",
    dependencies: Optional[List[str]] = None,
    min_laios_version: Optional[str] = None,
    tags: Optional[List[str]] = None,
)
```

### `to_dict`

```python
to_dict() -> Dict[str, Any]
```

Serializes to a dictionary.

---

## PluginRegistry

**Import:** `from laios.plugins.registry import PluginRegistry`

Central store for loaded plugins. Dispatches lifecycle hooks to all enabled plugins.

### Constructor

```python
PluginRegistry(event_bus: Optional[EventBus] = None)
```

### Plugin Lifecycle

#### `register`

```python
register(plugin: PluginBase) -> None
```

Registers a plugin instance. If a plugin with the same `name` already exists, it is unregistered first (calls `on_unload()`). Emits `PLUGIN_LOADED` event.

---

#### `unregister`

```python
unregister(name: str) -> bool
```

Calls `plugin.on_unload()`, sets `_loaded = False`, removes from registry. Emits `PLUGIN_UNLOADED` event. Returns `True` if found.

---

#### `unload_all`

```python
unload_all() -> None
```

Calls `unregister()` for every registered plugin. Used during agent shutdown.

---

### Enable/Disable

```python
enable_plugin(name: str) -> bool   # Sets plugin.enabled = True
disable_plugin(name: str) -> bool  # Sets plugin.enabled = False
```

Both return `True` if the plugin was found, `False` otherwise. Disabled plugins remain registered but are excluded from hook dispatch.

---

### Lookup

```python
get_plugin(name: str) -> Optional[PluginBase]
list_plugins(enabled_only: bool = False) -> List[PluginBase]
```

---

### Hook Dispatchers

The registry calls these automatically. They are also available for direct invocation in tests.

| Method | Calls |
|--------|-------|
| `dispatch_session_start(session_id, user_id)` | `plugin.on_session_start()` for all active plugins |
| `dispatch_session_end(session_id)` | `plugin.on_session_end()` |
| `dispatch_before_task(task_id, tool_name, parameters) -> Dict` | `plugin.on_before_task()` — chains parameter modifications |
| `dispatch_after_task(task_id, tool_name, success, result)` | `plugin.on_after_task()` |
| `dispatch_before_plan(goal_description)` | `plugin.on_before_plan()` |
| `dispatch_after_plan(plan_id, task_count)` | `plugin.on_after_plan()` |
| `dispatch_message(session_id, role, content) -> str` | `plugin.on_message()` — chains content modifications |

**Exception handling:** All dispatch methods catch exceptions from individual plugins, log them, and continue to the next plugin.

### Dunder Methods

```python
len(registry)          # Total number of registered plugins
"my_plugin" in registry  # True if registered
repr(registry)         # "<PluginRegistry(total=2, active=2)>"
```

---

## EventBus

**Import:** `from laios.plugins.events import EventBus, get_event_bus`

Thread-safe publish/subscribe event system. Used for inter-plugin communication and system-wide lifecycle events.

### Constructor

```python
EventBus(max_history: int = 100)
```

`max_history`: Maximum number of events to retain in history (oldest are dropped).

### `get_event_bus`

```python
get_event_bus() -> EventBus
```

Returns the global singleton `EventBus` instance. This is the same bus used by `AgentController`. Use this in plugins and scripts instead of creating a new `EventBus`.

---

### Subscription

#### `subscribe`

```python
subscribe(event_name: str, handler: Callable[[str, Dict], None]) -> None
```

Registers a handler for an event.

| Parameter | Type | Description |
|-----------|------|-------------|
| `event_name` | `str` | Exact event name, or a wildcard pattern |
| `handler` | `Callable` | Called with `(event_name: str, data: Dict)` |

**Wildcard patterns:**

| Pattern | Matches |
|---------|---------|
| `"task.started"` | Exact match only |
| `"task.*"` | All events starting with `"task."` |
| `"*"` | All events |

```python
event_bus.subscribe("task.*", lambda name, data: print(f"{name}: {data}"))
event_bus.subscribe("*", my_global_handler)
```

---

#### `unsubscribe`

```python
unsubscribe(event_name: str, handler: Callable) -> bool
```

Removes a specific handler. Returns `True` if found and removed.

---

### Emission

#### `emit`

```python
emit(
    event_name: str,
    data: Optional[Dict[str, Any]] = None,
    source: str = "system",
) -> None
```

Emits an event to all matching subscribers (exact, wildcard, and global `"*"`).

**Handler invocation order:** exact matches → wildcard matches → `"*"` matches.

**Exception handling:** Exceptions in handlers are caught and logged; they do not prevent other handlers from running.

---

### History

```python
get_history(
    event_name: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]
```

Returns recent event history as a list of dicts (`name`, `data`, `source`, `timestamp`).

```python
clear_history() -> None
```

```python
get_subscriber_count(event_name: Optional[str] = None) -> int
```

Returns total subscriber count (across all events if `event_name` is `None`).

---

### `clear_all`

```python
clear_all() -> None
```

Removes all subscriptions and clears event history. Use in tests to reset state between test cases.

---

## Built-in Event Names

**Import:** `from laios.plugins.events import <EVENT_NAME>`

| Constant | Value | Emitted When |
|----------|-------|--------------|
| `PLUGIN_LOADED` | `"plugin.loaded"` | Plugin registered in `PluginRegistry` |
| `PLUGIN_UNLOADED` | `"plugin.unloaded"` | Plugin unregistered |
| `SESSION_STARTED` | `"session.started"` | `AgentController.create_session()` called |
| `SESSION_ENDED` | `"session.ended"` | `AgentController.shutdown_session()` called |
| `TASK_STARTED` | `"task.started"` | Task execution begins |
| `TASK_COMPLETED` | `"task.completed"` | Task succeeds |
| `TASK_FAILED` | `"task.failed"` | Task fails |
| `PLAN_CREATED` | `"plan.created"` | Planner produces a plan |
| `MESSAGE_RECEIVED` | `"message.received"` | (reserved for future use) |
| `MESSAGE_SENT` | `"message.sent"` | (reserved for future use) |

**Event data payloads:**

| Event | `data` keys |
|-------|-------------|
| `session.started` | `session_id`, `user_id` |
| `session.ended` | `session_id` |
| `task.started` | `task_id`, `tool` |
| `task.completed` | `task_id`, `tool`, `success: True` |
| `task.failed` | `task_id`, `tool`, `success: False` |
| `plan.created` | `plan_id`, `task_count`, `goal` |
| `plugin.loaded` | `name`, `version` |
| `plugin.unloaded` | `name` |

---

## Plugin Discovery

Plugins are auto-discovered by `PluginLoader` on `AgentController` initialization.

**Filesystem layout:**

```
~/.laios/plugins/
└── my_plugin/
    └── plugin.py    ← must contain a PluginBase subclass
```

**Configuration:**

```yaml
plugins:
  enabled: true
  directories:
    - "~/.laios/plugins"
    - "./plugins"
  auto_load: false
```

**Discovery rules:**

1. For each directory in `directories`, scan for `*/plugin.py` files
2. Import each file and find `PluginBase` subclasses
3. Validate: `name`, `version`, `description` must be set
4. Resolve load order using dependency graph (topological sort)
5. Call `plugin.on_load(context)` and register in `PluginRegistry`

---

## Minimal Plugin Example

```python
# ~/.laios/plugins/hello_plugin/plugin.py
from laios.plugins.base import PluginBase, PluginContext

class HelloPlugin(PluginBase):
    name = "hello_plugin"
    version = "1.0.0"
    description = "Greets every new session"
    author = "demo"

    def on_load(self, context: PluginContext) -> None:
        print(f"HelloPlugin loaded. Model: {context.config.llm.model}")

    def on_session_start(self, session_id: str, user_id: str) -> None:
        print(f"Hello {user_id}! Session {session_id[:8]}... started.")
```

**Verify:**

```bash
laios plugins list
# → hello_plugin 1.0.0 - Greets every new session  [enabled]
```
