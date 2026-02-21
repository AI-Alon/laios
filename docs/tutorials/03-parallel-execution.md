# Tutorial 3: Parallel Task Execution

The `Executor` can run multiple independent tasks at the same time using `asyncio.gather()`. This tutorial shows how to build tasks manually, run them in parallel, inspect per-task metrics, and use the retry and context manager patterns.

**Time:** ~20 minutes
**Difficulty:** Intermediate
**Prerequisite:** [Tutorial 1: Your First Agent](01-first-agent.md)

---

## Prerequisites

- LAIOS installed: `pip install -e ".[llm]"`
- No LLM required for direct executor usage

---

## Step 1: Set Up the Registry and Executor

```python
import asyncio
from laios.tools.registry import ToolRegistry
from laios.tools.builtin import ALL_BUILTIN_TOOLS
from laios.execution.executor import Executor, ResourceLimits
from laios.core.types import Task, Context

# Set up tools
registry = ToolRegistry()
registry.register_tools(ALL_BUILTIN_TOOLS)
print(f"Tools registered: {len(registry)}")

# Create executor with a 30-second timeout and 4 worker threads
limits = ResourceLimits(timeout_seconds=30)
executor = Executor(
    tool_registry=registry,
    resource_limits=limits,
    max_workers=4,
    enable_monitoring=True,
)

# Create execution context
context = Context(session_id="tutorial-03", user_id="demo")
```

---

## Step 2: Build Tasks Manually

Tasks normally come from the `Planner`, but you can create them directly for testing or scripting:

```python
PLAN_ID = "demo-plan-01"

tasks = [
    Task(
        plan_id=PLAN_ID,
        description="Read README.md",
        tool_name="filesystem.read_file",
        parameters={"path": "README.md"},
    ),
    Task(
        plan_id=PLAN_ID,
        description="List current directory",
        tool_name="filesystem.list_directory",
        parameters={"path": "."},
    ),
    Task(
        plan_id=PLAN_ID,
        description="Read config file",
        tool_name="filesystem.read_file",
        parameters={"path": "config/default.yaml"},
    ),
]

print(f"\nTasks created: {len(tasks)}")
for t in tasks:
    print(f"  - {t.description} → {t.tool_name}")
```

---

## Step 3: Execute in Parallel

`execute_parallel()` is an async method. Use `asyncio.run()` to call it from synchronous code:

```python
print("\nRunning tasks in parallel...")
results = asyncio.run(executor.execute_parallel(tasks, context))

print(f"\nResults ({len(results)} total):")
for result in results:
    status = "OK" if result.success else "FAIL"
    time_ms = result.execution_time_seconds * 1000
    print(f"  [{status}] {result.task_id[:8]} — {time_ms:.0f}ms")
    if result.success and result.output:
        output_preview = str(result.output)[:80]
        print(f"       {output_preview}...")
    elif not result.success:
        print(f"       Error: {result.error}")
```

**Key point:** The results list is in the **same order** as the input `tasks` list, even though tasks ran concurrently.

---

## Step 4: Single Task with Progress Callback

Use `on_progress` to get live feedback during a single task:

```python
def on_progress(event: str, data: dict):
    task_id = data.get("task_id", "?")[:8]
    print(f"  [Progress] {event}: task={task_id}")

single_task = Task(
    plan_id=PLAN_ID,
    description="Get file info",
    tool_name="filesystem.get_info",
    parameters={"path": "README.md"},
)

print("\nRunning single task with progress callback...")
result = executor.execute_task(single_task, context, on_progress=on_progress)

print(f"Result: success={result.success}, time={result.execution_time_seconds:.3f}s")
if result.success:
    print(f"Output: {result.output}")
```

---

## Step 5: Inspect Execution Metrics

After tasks run, the `TaskMonitor` retains their metrics:

```python
all_metrics = executor.get_all_metrics()
print(f"\nMetrics collected: {len(all_metrics)}")

for m in all_metrics:
    print(f"  Task {m.task_id[:8]}:")
    print(f"    Execution time: {m.execution_time:.3f}s")
    print(f"    Checkpoints: {len(m.checkpoints)}")
    for cp in m.checkpoints:
        print(f"      - {cp['name']}")
```

---

## Step 6: Execute with Retry

For tasks that may fail transiently (network requests, file locks), use `execute_with_retry()`:

```python
retry_task = Task(
    plan_id=PLAN_ID,
    description="Fetch a web resource (may fail)",
    tool_name="web.fetch",
    parameters={"url": "https://httpbin.org/status/200"},
)

print("\nRunning task with retry (max 3 attempts)...")
result = executor.execute_with_retry(
    task=retry_task,
    context=context,
    max_retries=3,
    retry_delay=0.5,
)

retries_used = result.metadata.get("retries", 0)
exhausted = result.metadata.get("retry_exhausted", False)

print(f"Success: {result.success}")
print(f"Retries used: {retries_used}")
print(f"Retry exhausted: {exhausted}")
```

---

## Step 7: Context Manager Pattern

The `Executor` supports the context manager protocol to ensure the thread pool is always shut down:

```python
print("\nUsing context manager...")

with Executor(registry, resource_limits=ResourceLimits(timeout_seconds=10)) as ex:
    tasks_to_run = [
        Task(
            plan_id="cm-plan",
            description="Read README",
            tool_name="filesystem.read_file",
            parameters={"path": "README.md"},
        ),
    ]
    r = ex.execute_task(tasks_to_run[0], context)
    print(f"Result inside context manager: success={r.success}")

# Thread pool is automatically shut down here
print("Executor shut down (thread pool cleaned up).")
```

---

## Step 8: Async Task (Coroutine)

For use inside an existing async application:

```python
async def run_async_task():
    task = Task(
        plan_id=PLAN_ID,
        description="List directory async",
        tool_name="filesystem.list_directory",
        parameters={"path": "."},
    )
    result = await executor.execute_async(task, context)
    print(f"Async result: success={result.success}, items={len(result.output or [])}")

asyncio.run(run_async_task())
```

---

## Cleanup

```python
executor.shutdown(wait=True)
print("\nExecutor shutdown complete.")
```

---

## Complete Script

Save as `tutorial_03.py` and run `python tutorial_03.py` (no Ollama needed):

```python
import asyncio
from laios.tools.registry import ToolRegistry
from laios.tools.builtin import ALL_BUILTIN_TOOLS
from laios.execution.executor import Executor, ResourceLimits
from laios.core.types import Task, Context

registry = ToolRegistry()
registry.register_tools(ALL_BUILTIN_TOOLS)

limits = ResourceLimits(timeout_seconds=30)

with Executor(registry, resource_limits=limits, max_workers=4) as executor:
    context = Context(session_id="demo", user_id="demo")
    PLAN_ID = "demo-plan"

    tasks = [
        Task(plan_id=PLAN_ID, description="Read README",
             tool_name="filesystem.read_file", parameters={"path": "README.md"}),
        Task(plan_id=PLAN_ID, description="List directory",
             tool_name="filesystem.list_directory", parameters={"path": "."}),
    ]

    # Parallel
    results = asyncio.run(executor.execute_parallel(tasks, context))
    for r in results:
        status = "OK" if r.success else "FAIL"
        print(f"[{status}] {r.task_id[:8]} — {r.execution_time_seconds:.3f}s")

    # Metrics
    for m in executor.get_all_metrics():
        print(f"  Metrics for {m.task_id[:8]}: {m.execution_time:.3f}s, "
              f"{len(m.checkpoints)} checkpoints")
```

---

## Next Steps

- **[Tutorial 4: Building Plugins](04-building-plugins.md)** — extend the agent
- **[Execution API Reference](../api/execution.md)** — complete API docs
