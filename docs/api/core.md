# Core API Reference

The `laios.core` package contains the agent controller, session management, configuration, and all fundamental data types.

---

## AgentController

**Import:** `from laios.core.agent import AgentController`

The main orchestration hub for LAIOS. Initializes all subsystems and provides the primary interface for session management, chat, and goal execution.

### Constructor

```python
AgentController(config: Config)
```

Initializes the full LAIOS stack:

1. LLM client (Ollama, OpenAI, or Anthropic, based on `config.llm.provider`)
2. `ToolRegistry` with all built-in tools pre-registered
3. `Reasoner`, `Planner`, `Executor`, `MemoryStore`, `Reflector`
4. `EventBus`, `PluginRegistry` (auto-discovers and loads plugins)
5. Production hardening: `InputSanitizer`, `CircuitBreaker` (LLM), `HealthChecker`, `GracefulShutdown`
6. Configuration validation (logs warnings/errors; does not raise on invalid config)

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `Config` | Root configuration object |

**Side effects:** Loads plugins from directories listed in `config.plugins.directories`. Registers `tools` and `memory` health checks. Registers shutdown hooks for the plugin registry and executor.

---

### Session Management

#### `create_session`

```python
create_session(user_id: str, config: Optional[Config] = None) -> Session
```

Creates a new agent session with a randomly generated UUID session ID.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | `str` | required | Identifier for the user |
| `config` | `Optional[Config]` | `None` | Per-session config override; falls back to the agent's root config |

**Returns:** `Session`

**Side effects:** Dispatches `SESSION_STARTED` event on the `EventBus`. Calls `on_session_start()` on all loaded plugins.

---

#### `get_session`

```python
get_session(session_id: str) -> Optional[Session]
```

Retrieves an active session by ID. Returns `None` if the session does not exist or has been shut down.

---

#### `shutdown_session`

```python
shutdown_session(session_id: str) -> None
```

Gracefully closes a session and removes it from memory.

**Side effects:** Dispatches `SESSION_ENDED` event. Calls `on_session_end()` on all plugins. Sets `session.active = False`.

---

### Conversation

#### `process_message`

```python
process_message(session_id: str, user_message: str) -> str
```

Processes a user message through the full chat pipeline and returns a response string.

**Pipeline:**

1. Adds user message to session context and short-term memory
2. On the first message of a session, retrieves up to 3 relevant memories and injects them into the system prompt
3. Builds the message list (system prompt + conversation history)
4. Calls the LLM via `CircuitBreaker` — on `CircuitBreakerError`, returns an error string (does not raise)
5. Adds the assistant response to session context and short-term memory
6. Returns the response string

**Raises:** `ValueError` if `session_id` is not found.

**Note:** If the LLM client failed to initialize, returns a human-readable error message instead of raising.

---

#### `process_message_stream`

```python
process_message_stream(session_id: str, user_message: str) -> Generator[str, None, None]
```

Same pipeline as `process_message` but yields text chunks as the LLM generates them (real-time streaming).

**Yields:** `str` — text chunks

**Usage:**

```python
for chunk in agent.process_message_stream(session.id, "Tell me a story"):
    print(chunk, end="", flush=True)
```

After the generator is exhausted, the full response has been stored in session context and short-term memory.

**Raises:** `ValueError` if `session_id` is not found.

---

### Goal Execution

#### `execute_goal`

```python
execute_goal(session_id: str, goal: Goal) -> Dict
```

Executes a structured goal through the full reason → plan → execute → reflect pipeline.

**Pipeline:**

1. Creates a plan via `Planner.create_plan(goal, context)`
2. Dispatches `PLAN_CREATED` event with `plan_id`, `task_count`, and `goal`
3. If `trust_level == PARANOID`: returns immediately with `awaiting_approval: True` — no tasks are executed
4. Sets `plan.status = EXECUTING` and executes ready tasks in dependency order
5. For each failed task: calls `Reflector.evaluate_task()`. If `evaluation.should_replan` is `True` and replanning attempts remain, calls `Planner.replan()` and restarts the execution loop
6. Stores an `Episode` in `MemoryStore`
7. Calls `Reflector.evaluate_plan()` on all results

**Returns:** `Dict` with keys:

| Key | Type | Description |
|-----|------|-------------|
| `goal` | `dict` | `goal.model_dump()` |
| `plan` | `dict` | `plan.model_dump()` |
| `results` | `list[dict]` | List of `TaskResult.model_dump()` |
| `success` | `bool` | `True` if all tasks succeeded |
| `episode_id` | `str` | UUID of stored episode |
| `replanning_attempts` | `int` | Number of times replanning was triggered |
| `awaiting_approval` | `bool` | Present and `True` when `trust_level == PARANOID` |
| `message` | `str` | Human-readable description (on no-tasks or approval-required) |

**Raises:** `ValueError` if `session_id` is not found.

---

### State & Subsystems

#### `get_session_state`

```python
get_session_state(session_id: str) -> Dict
```

Returns a snapshot of the session's current state.

**Returns dict with keys:** `session_id`, `user_id`, `active`, `message_count`, `llm_available`, `reflection_enabled`, `tools_registered`, `context`.

---

#### Subsystem Accessors

```python
get_tool_registry() -> ToolRegistry
get_memory() -> MemoryStore
get_reflector() -> Optional[Reflector]
get_plugin_registry() -> PluginRegistry
get_event_bus() -> EventBus
get_health_checker() -> HealthChecker
get_shutdown_manager() -> GracefulShutdown
```

---

## Session

**Import:** `from laios.core.agent import Session`

Represents an active agent session. Holds the conversation context and user identity.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | UUID session identifier |
| `user_id` | `str` | User identifier |
| `config` | `Config` | Active configuration for this session |
| `context` | `Context` | Conversation context (messages, memories) |
| `active` | `bool` | `False` after `shutdown_session()` |

### Methods

```python
add_message(message: Message) -> None
```
Appends a message to `session.context.messages`.

```python
get_context() -> Context
```
Returns the current `Context` object.

```python
get_conversation_history() -> List[LLMMessage]
```
Returns the conversation as a list of `LLMMessage` objects, suitable for passing directly to an `LLMClient.generate()` call.

---

## Configuration Types

### Config

**Import:** `from laios.core.types import Config`

Root configuration model (Pydantic `BaseModel`).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `llm` | `LLMConfig` | `LLMConfig()` | LLM provider settings |
| `agent` | `AgentConfig` | `AgentConfig()` | Agent behavior settings |
| `memory` | `MemoryConfig` | `MemoryConfig()` | Memory system settings |
| `tools` | `Dict[str, Any]` | `{}` | Tool permission overrides |
| `execution` | `Dict[str, Any]` | `{}` | Executor settings |
| `logging` | `Dict[str, Any]` | `{}` | Logging settings |

#### `from_yaml`

```python
@classmethod
from_yaml(path: str) -> Config
```

Loads and validates a YAML configuration file. Expands `~` in the path.

```python
config = Config.from_yaml("config/default.yaml")
config = Config.from_yaml("~/.laios/config.yaml")
```

**Raises:** `FileNotFoundError`, `yaml.YAMLError`, or Pydantic `ValidationError` on invalid config.

---

### LLMConfig

**Import:** `from laios.core.types import LLMConfig`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `provider` | `str` | `"ollama"` | `"ollama"`, `"openai"`, or `"anthropic"` |
| `model` | `str` | `"llama2"` | Model name (e.g., `"gemma3:4b"`, `"gpt-4o"`) |
| `base_url` | `str` | `"http://localhost:11434"` | Base URL for Ollama-compatible endpoints |
| `temperature` | `float` | `0.7` | Sampling temperature (`0.0`–`2.0`) |
| `max_tokens` | `int` | `2048` | Maximum tokens to generate (≥ 1) |
| `timeout` | `int` | `60` | Request timeout in seconds (≥ 1) |
| `keep_alive` | `str` | `"30m"` | Ollama model keep-alive duration |
| `num_ctx` | `Optional[int]` | `None` | Context window size for Ollama (e.g., `4096`) |

---

### AgentConfig

**Import:** `from laios.core.types import AgentConfig`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `trust_level` | `TrustLevel` | `TrustLevel.BALANCED` | Agent autonomy level |
| `max_planning_iterations` | `int` | `3` | Max iterations for plan refinement (≥ 1) |
| `max_replanning_attempts` | `int` | `2` | Max times the agent will replan after failure (≥ 0) |
| `enable_reflection` | `bool` | `True` | Whether to evaluate tasks and plans via the Reflector |

---

### MemoryConfig

**Import:** `from laios.core.types import MemoryConfig`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `short_term` | `Dict[str, Any]` | `{}` | Short-term memory settings (e.g., `{"max_messages": 50}`) |
| `long_term` | `Dict[str, Any]` | `{}` | Long-term memory settings |
| `episodic` | `Dict[str, Any]` | `{}` | Episodic memory settings |

---

## Core Data Types

All core types are Pydantic `BaseModel` subclasses unless noted.

### Goal

```python
class Goal(BaseModel):
    id: str                          # Auto-generated UUID
    description: str                 # Natural language objective
    constraints: Dict[str, Any]      # e.g., {"max_time_seconds": 300}
    context: Dict[str, Any]          # Additional context key-values
    priority: int                    # 1 (lowest) to 10 (highest), default 5
    created_at: datetime             # Auto-set on creation
```

**Usage:**

```python
from laios.core.types import Goal

goal = Goal(
    description="Analyze all Python files and report code quality issues",
    constraints={"max_time_seconds": 120},
    priority=8,
)
```

---

### Plan

```python
class Plan(BaseModel):
    id: str                          # Auto-generated UUID
    goal: Goal                       # The goal this plan fulfills
    tasks: List[Task]                # Ordered list of tasks (DAG)
    status: PlanStatus               # Current plan status
    created_at: datetime
    approved_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    metadata: Dict[str, Any]
```

**Methods:**

```python
get_task(task_id: str) -> Optional[Task]
```
Finds and returns a task by ID. Returns `None` if not found.

```python
get_ready_tasks() -> List[Task]
```
Returns all `PENDING` tasks whose dependencies are all `COMPLETED`. Used by the `Executor` to determine what can run next.

---

### Task

```python
class Task(BaseModel):
    id: str                          # Auto-generated UUID
    plan_id: str                     # ID of the parent plan
    description: str                 # Human-readable description
    tool_name: str                   # Tool to invoke (e.g., "filesystem.read_file")
    parameters: Dict[str, Any]       # Tool input parameters
    dependencies: List[str]          # Task IDs that must complete first
    status: TaskStatus               # Current status
    result: Optional[Any]            # Set after successful execution
    error: Optional[str]             # Set after failed execution
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    metadata: Dict[str, Any]
```

---

### TaskResult

```python
class TaskResult(BaseModel):
    task_id: str
    success: bool
    output: Any                      # Tool output data (on success)
    error: Optional[str]             # Error message (on failure)
    logs: List[str]                  # Execution log lines
    execution_time_seconds: float    # Wall-clock time
    metadata: Dict[str, Any]         # Extra data (metrics, retries, etc.)
```

---

### Message

```python
class Message(BaseModel):
    id: str                          # Auto-generated UUID
    role: str                        # "user", "assistant", "system", or "tool"
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
```

---

### Memory

```python
class Memory(BaseModel):
    id: str                          # Auto-generated UUID
    content: str
    memory_type: MemoryType          # SHORT_TERM, LONG_TERM, or EPISODIC
    embedding: Optional[List[float]] # Vector embedding (if applicable)
    metadata: Dict[str, Any]
    created_at: datetime
    accessed_at: datetime
```

---

### Episode

```python
class Episode(BaseModel):
    id: str                          # Auto-generated UUID
    session_id: str
    plan: Plan                       # The plan that was executed
    results: List[TaskResult]        # One result per task
    success: bool                    # True if all tasks succeeded
    created_at: datetime
    metadata: Dict[str, Any]
```

---

### Evaluation

```python
class Evaluation(BaseModel):
    task_id: Optional[str]           # Set for task evaluations
    plan_id: Optional[str]           # Set for plan evaluations
    success: bool
    confidence: float                # 0.0–1.0
    issues: List[str]                # Detected problems
    suggestions: List[str]           # Improvement suggestions
    should_replan: bool              # Whether replanning is recommended
```

---

### Context

```python
class Context(BaseModel):
    session_id: str
    user_id: str
    messages: List[Message]          # Conversation history
    relevant_memories: List[Memory]  # Memories retrieved for current request
    metadata: Dict[str, Any]
```

---

## Enums

### TaskStatus

```python
class TaskStatus(str, Enum):
    PENDING   = "pending"    # Waiting to be executed
    RUNNING   = "running"    # Currently executing
    COMPLETED = "completed"  # Finished successfully
    FAILED    = "failed"     # Finished with an error
    CANCELLED = "cancelled"  # Explicitly cancelled
    BLOCKED   = "blocked"    # Waiting on unresolved dependencies
```

### PlanStatus

```python
class PlanStatus(str, Enum):
    DRAFT     = "draft"      # Just created, not yet approved
    APPROVED  = "approved"   # Approved but not started
    EXECUTING = "executing"  # Currently running
    COMPLETED = "completed"  # All tasks finished successfully
    FAILED    = "failed"     # One or more tasks failed
    CANCELLED = "cancelled"  # Execution stopped
```

### TrustLevel

```python
class TrustLevel(str, Enum):
    PARANOID   = "paranoid"   # Plan shown; execution requires manual approval
    BALANCED   = "balanced"   # Auto-executes; confirms risky operations (default)
    AUTONOMOUS = "autonomous" # Auto-executes everything without confirmation
```

**Effect on `execute_goal()`:** With `PARANOID`, `execute_goal()` returns immediately with `awaiting_approval: True` and an empty `results` list. No tasks are run.

### Permission

```python
class Permission(str, Enum):
    FILESYSTEM_READ  = "filesystem.read"
    FILESYSTEM_WRITE = "filesystem.write"
    SHELL_EXECUTE    = "shell.execute"
    NETWORK_ACCESS   = "network.access"
    CODE_EXECUTE     = "code.execute"
```

Used by tools to declare what they require, and by the config to restrict what is allowed.

### MemoryType

```python
class MemoryType(str, Enum):
    SHORT_TERM = "short_term"  # In-memory conversation buffer
    LONG_TERM  = "long_term"   # Persistent JSON file on disk
    EPISODIC   = "episodic"    # Per-episode JSON files on disk
```
