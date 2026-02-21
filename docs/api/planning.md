# Planning API Reference

The `laios.planning` package converts natural language goals into executable DAG (Directed Acyclic Graph) plans.

---

## Planner

**Import:** `from laios.planning.planner import Planner`

The Planner uses an LLM to decompose a `Goal` into a structured `Plan` of `Task` objects with dependency relationships. `AgentController` creates and uses one automatically.

### Constructor

```python
Planner(
    tool_registry: Optional[ToolRegistry] = None,
    llm_client: Optional[LLMClient] = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tool_registry` | `Optional[ToolRegistry]` | `None` | Registry of available tools, used to tell the LLM what tools exist |
| `llm_client` | `Optional[LLMClient]` | `None` | LLM to use for plan generation |

**Note:** If `llm_client` is `None`, `create_plan()` returns an empty plan.

---

### Methods

#### `create_plan`

```python
create_plan(goal: Goal, context: Context) -> Plan
```

Generates an execution plan for the given goal.

**How it works:**

1. Formats the list of available tools from `tool_registry.get_all_schemas()`
2. Calls the LLM with a task-generation prompt that includes the goal description, constraints, and available tools
3. Parses the LLM response into a list of `Task` objects with dependencies
4. Builds a `NetworkX` DAG from the dependencies and validates there are no cycles
5. Returns a `Plan` with `status=DRAFT`

**Returns:** `Plan` — may have `tasks=[]` if the LLM is unavailable or returns an unparseable response.

```python
from laios.planning.planner import Planner
from laios.core.types import Goal, Context

planner = Planner(tool_registry=registry, llm_client=llm_client)
goal = Goal(description="Find all TODO comments in Python files")
context = Context(session_id="s1", user_id="alice")

plan = planner.create_plan(goal, context)
print(f"Tasks: {len(plan.tasks)}")
for task in plan.tasks:
    print(f"  - {task.description} → {task.tool_name}")
```

---

#### `replan`

```python
replan(plan: Plan, failure_context: Dict[str, Any]) -> Plan
```

Generates a revised plan after a task failure.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `plan` | `Plan` | The original plan that partially failed |
| `failure_context` | `Dict` | Information about the failure: `failed_task_id`, `error`, `evaluation` |

**How it works:**

1. Calls the LLM with a replanning prompt including the original plan, completed tasks, the failed task, and the error
2. Parses and returns a revised `Plan`
3. If the LLM returns an unparseable response, returns the original plan unchanged

**Returns:** `Plan` — a new or modified plan.

```python
failure_context = {
    "failed_task_id": task.id,
    "error": "File not found: /tmp/data.csv",
    "evaluation": evaluation.model_dump(),
}
new_plan = planner.replan(plan, failure_context)
```

---

#### `decompose_task`

```python
decompose_task(task: Task, context: Context) -> List[Task]
```

Breaks a single complex task into multiple subtasks using the LLM.

**Returns:** List of `Task` objects. Returns `[task]` (the original task unchanged) if the LLM is unavailable.

---

#### `resolve_dependencies`

```python
resolve_dependencies(plan: Plan) -> None
```

Validates the plan's task dependencies using `NetworkX`. Raises an exception if circular dependencies are detected.

Called automatically within `create_plan()`. Exposed as a public method for use in tests or when manually constructing plans.

---

## Plan Execution Model

The `Plan` type (defined in `laios.core.types`) is a DAG:

- Tasks with no `dependencies` can run immediately
- A task becomes eligible when all its `dependencies` (by task ID) have `status=COMPLETED`
- `plan.get_ready_tasks()` returns the currently eligible tasks

The `Executor` uses `get_ready_tasks()` in a loop until all tasks are complete or failed.

```
Goal: "Analyze Python files and report issues"

Plan DAG:
  Task A: filesystem.list_directory (no deps)
       ↓
  Task B: filesystem.read_file (depends on A)
       ↓
  Task C: python.execute — analyze (depends on B)
       ↓
  Task D: filesystem.write_file — write report (depends on C)
```

---

## Integration with AgentController

`AgentController` orchestrates the full cycle:

```python
# Internally in AgentController.execute_goal():
plan = self._planner.create_plan(goal, session.context)

# On failure:
new_plan = self._planner.replan(plan, failure_context)
```

You can also use the `Planner` directly without an `AgentController`:

```python
from laios.planning.planner import Planner
from laios.tools.registry import ToolRegistry
from laios.tools.builtin import ALL_BUILTIN_TOOLS
from laios.llm.providers.ollama import OllamaClient

registry = ToolRegistry()
registry.register_tools(ALL_BUILTIN_TOOLS)

client = OllamaClient(model="llama2")
planner = Planner(tool_registry=registry, llm_client=client)
```
