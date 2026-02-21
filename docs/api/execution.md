# Execution API Reference

The `laios.execution` package handles task invocation, timeout enforcement, retry logic, parallel execution, and real-time metrics collection.

---

## Executor

**Import:** `from laios.execution.executor import Executor`

Runs `Task` objects by invoking tools from a `ToolRegistry`. Supports synchronous, asynchronous, and parallel execution with monitoring.

### Constructor

```python
Executor(
    tool_registry: ToolRegistry,
    resource_limits: Optional[ResourceLimits] = None,
    max_workers: int = 4,
    enable_monitoring: bool = True,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tool_registry` | `ToolRegistry` | required | Registry to look up and invoke tools |
| `resource_limits` | `Optional[ResourceLimits]` | `None` | Default resource constraints (uses `ResourceLimits()` if `None`) |
| `max_workers` | `int` | `4` | `ThreadPoolExecutor` thread count for async/parallel operations |
| `enable_monitoring` | `bool` | `True` | Whether to track metrics via `TaskMonitor` |

**Side effects:** Creates an internal `ThreadPoolExecutor`. Always call `shutdown()` or use the context manager.

---

### Context Manager

```python
with Executor(registry, max_workers=4) as executor:
    result = executor.execute_task(task, context)
# ThreadPoolExecutor is shut down automatically
```

---

### Execution Methods

#### `execute_task`

```python
execute_task(
    task: Task,
    context: Context,
    timeout: Optional[float] = None,
    on_progress: Optional[Callable[[str, Any], None]] = None,
) -> TaskResult
```

Executes a single task synchronously. Uses the thread pool with `future.result(timeout=...)` to enforce the timeout.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `task` | `Task` | required | Task to execute |
| `context` | `Context` | required | Current execution context |
| `timeout` | `Optional[float]` | `None` | Seconds before timeout; overrides `resource_limits.timeout_seconds` |
| `on_progress` | `Optional[Callable]` | `None` | Called with `(event: str, data: dict)` at key moments |

**`on_progress` events:**

| Event | When |
|-------|------|
| `"started"` | Before tool invocation |
| `"completed"` | After successful execution |
| `"failed"` | After an exception |
| `"timeout"` | When the timeout is exceeded |

**Returns:** `TaskResult` — always. Never raises. Sets `task.status` to `COMPLETED` or `FAILED`.

**Side effects:** Updates `task.status`, `task.started_at`, `task.completed_at`, `task.result`, `task.error`.

---

#### `execute_async`

```python
async execute_async(
    task: Task,
    context: Context,
    timeout: Optional[float] = None,
    on_progress: Optional[Callable[[str, Any], None]] = None,
) -> TaskResult
```

Async wrapper around `execute_task()`. Runs the synchronous execution in the thread pool via `asyncio.get_event_loop().run_in_executor()`.

```python
import asyncio

result = asyncio.run(executor.execute_async(task, context))
```

---

#### `execute_parallel`

```python
async execute_parallel(
    tasks: List[Task],
    context: Context,
    timeout: Optional[float] = None,
    on_progress: Optional[Callable[[str, Any], None]] = None,
) -> List[TaskResult]
```

Executes multiple tasks concurrently using `asyncio.gather()`. Results are returned in the same order as the input `tasks` list.

If a task raises an unexpected exception (rather than returning a failure `ToolOutput`), it is caught and wrapped in a `TaskResult(success=False, error=str(exception))`.

```python
import asyncio

results = asyncio.run(executor.execute_parallel(tasks, context))
for r in results:
    print(f"Task {r.task_id[:8]}: success={r.success}, time={r.execution_time_seconds:.2f}s")
```

---

#### `execute_with_retry`

```python
execute_with_retry(
    task: Task,
    context: Context,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    on_progress: Optional[Callable[[str, Any], None]] = None,
) -> TaskResult
```

Retries the task up to `max_retries` times on failure, with `retry_delay` seconds between attempts.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_retries` | `int` | `3` | Total additional attempts after the first (so max `max_retries + 1` total runs) |
| `retry_delay` | `float` | `1.0` | Seconds to wait between retries |

**Returns:** The first successful `TaskResult`, or the last failure if all attempts fail. On exhaustion, `result.metadata` contains:

```python
{
    "retries": max_retries,
    "retry_exhausted": True,
}
```

```python
result = executor.execute_with_retry(task, context, max_retries=3, retry_delay=0.5)
print(f"Retries used: {result.metadata.get('retries', 0)}")
```

---

### Monitoring Methods

#### `get_running_tasks`

```python
get_running_tasks() -> List[Task]
```

Returns tasks currently in `RUNNING` status. Returns `[]` if `enable_monitoring=False`.

---

#### `get_task_status`

```python
get_task_status(task_id: str) -> Optional[TaskStatus]
```

Returns the current `TaskStatus` for a running task. Returns `None` if not found or monitoring is disabled.

---

#### `get_metrics`

```python
get_metrics(task_id: str) -> Optional[ExecutionMetrics]
```

Returns `ExecutionMetrics` for a specific task (after it has been monitored). Returns `None` if not found.

---

#### `get_all_metrics`

```python
get_all_metrics() -> List[ExecutionMetrics]
```

Returns metrics for all tasks that have been monitored since the executor was created.

---

### Cancellation

#### `cancel_task`

```python
cancel_task(task_id: str) -> bool
```

Registers a cancellation request for a running task. Returns `True` if registered.

**Important:** Cancellation is cooperative. The executor checks for cancellation before and after tool invocation. Tools that have already started are not interrupted mid-execution.

---

### Lifecycle

#### `shutdown`

```python
shutdown(wait: bool = True) -> None
```

Shuts down the internal `ThreadPoolExecutor`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `wait` | `bool` | `True` | `True` waits for running tasks to finish; `False` returns immediately |

---

## ResourceLimits

**Import:** `from laios.execution.executor import ResourceLimits`

Defines constraints for task execution.

### Constructor

```python
ResourceLimits(
    timeout_seconds: Optional[float] = None,
    memory_limit_mb: Optional[int] = None,
    cpu_limit_percent: Optional[float] = None,
)
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `timeout_seconds` | `Optional[float]` | `None` | Max wall-clock seconds per task (`None` = no limit) |
| `memory_limit_mb` | `Optional[int]` | `None` | Memory ceiling in MB (informational; not enforced at the OS level) |
| `cpu_limit_percent` | `Optional[float]` | `None` | CPU ceiling percentage (informational) |

### `from_config`

```python
@classmethod
from_config(cls, config: Dict[str, Any]) -> ResourceLimits
```

Creates a `ResourceLimits` from a config dictionary (keys: `timeout_seconds`, `memory_limit_mb`, `cpu_limit_percent`).

```python
limits = ResourceLimits.from_config({"timeout_seconds": 30, "memory_limit_mb": 256})
```

---

## ExecutionMetrics

**Import:** `from laios.execution.executor import ExecutionMetrics`

Metrics collected during task execution. Obtained via `executor.get_metrics(task_id)`.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `task_id` | `str` | Task identifier |
| `start_time` | `Optional[float]` | Unix timestamp of start |
| `end_time` | `Optional[float]` | Unix timestamp of end |
| `execution_time` | `float` | Wall-clock seconds |
| `cpu_time` | `float` | CPU time (not currently measured; always `0.0`) |
| `memory_peak_mb` | `float` | Peak memory (not currently measured; always `0.0`) |
| `retries` | `int` | Number of retries |
| `checkpoints` | `List[Dict]` | Named execution milestones |

### Methods

```python
checkpoint(name: str, data: Optional[Dict] = None) -> None
```
Adds a named checkpoint with a timestamp.

```python
to_dict() -> Dict[str, Any]
```
Serializes the metrics to a dictionary.

---

## TaskMonitor

**Import:** `from laios.execution.executor import TaskMonitor`

Tracks running tasks and collects metrics. The `Executor` uses one internally when `enable_monitoring=True`. Available for standalone use in tests or custom orchestration.

### Constructor

```python
TaskMonitor()
```

### Methods

```python
start_monitoring(task: Task) -> ExecutionMetrics
stop_monitoring(task_id: str) -> Optional[ExecutionMetrics]
get_running_tasks() -> List[Task]
get_task_status(task_id: str) -> Optional[TaskStatus]
get_metrics(task_id: str) -> Optional[ExecutionMetrics]
get_all_metrics() -> List[ExecutionMetrics]
checkpoint(task_id: str, name: str, data: Optional[Dict] = None) -> None
is_running(task_id: str) -> bool
clear_metrics(task_id: Optional[str] = None) -> None
```

All methods are thread-safe (protected by an internal `threading.Lock`).

---

## ExecutionMode

**Import:** `from laios.execution.executor import ExecutionMode`

```python
class ExecutionMode(str, Enum):
    SYNC     = "sync"
    ASYNC    = "async"
    PARALLEL = "parallel"
```

Used as metadata in configs and status displays.

---

## Global Monitors

**Import:** `from laios.execution.monitor import get_execution_monitor, get_performance_monitor`

Singleton monitors available for system-wide tracking (used by the REST API and `laios status` command).

```python
from laios.execution.monitor import get_execution_monitor, get_performance_monitor

monitor = get_execution_monitor()
perf = get_performance_monitor()

# Track custom progress
monitor.update_task_progress(task_id, percent=50, message="Halfway done")

# Record custom metric
perf.record_metric(task_id, "response_time", 1.23, "seconds")
summary = perf.get_metric_summary(task_id, "response_time")
# -> {"min": ..., "max": ..., "avg": ..., "count": ...}
```
