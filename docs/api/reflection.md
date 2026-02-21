# Reflection API Reference

The `laios.reflection` package provides self-evaluation of task and plan execution, failure pattern detection, and learning from experience.

---

## Reflector

**Import:** `from laios.reflection.reflector import Reflector`

Analyzes task and plan outcomes, identifies failure patterns, and generates improvement suggestions. `AgentController` creates one automatically when `config.agent.enable_reflection = True`.

### Constructor

```python
Reflector(
    llm_client: LLMClient,
    criteria: Optional[ReflectionCriteria] = None,
    enable_llm_reflection: bool = True,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `llm_client` | `LLMClient` | required | LLM used for generating evaluations |
| `criteria` | `Optional[ReflectionCriteria]` | `None` | Evaluation thresholds; uses `ReflectionCriteria()` defaults if `None` |
| `enable_llm_reflection` | `bool` | `True` | Whether to use the LLM for richer evaluations (set to `False` for faster rule-based evaluation) |

---

### Methods

#### `evaluate_task`

```python
evaluate_task(task: Task, result: TaskResult) -> Evaluation
```

Evaluates the outcome of a single task execution.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task` | `Task` | The task that was executed |
| `result` | `TaskResult` | The execution result |

**Returns:** `Evaluation` with:

- `success`: `True` if the task succeeded
- `confidence`: Float 0.0–1.0 indicating evaluation certainty
- `issues`: List of detected problems
- `suggestions`: List of improvement ideas
- `should_replan`: `True` if the failure warrants generating a new plan

**`should_replan` triggers:** Set to `True` for errors categorized as: `timeout`, `not_found`, `network`, `resource`. Set to `False` for: `permission`, `validation`, `execution` (these typically won't be fixed by replanning).

**Error categories and default suggestions:**

| Category | Detection | Suggested fix |
|----------|-----------|---------------|
| `timeout` | `"timeout"` in error | Increase timeout or break into smaller tasks |
| `permission` | `"permission"` / `"access denied"` | Check required permissions in config |
| `not_found` | `"not found"` / `"no such file"` | Verify paths exist before accessing |
| `network` | `"connection"` / `"network"` | Check network connectivity |
| `validation` | `"validation"` / `"invalid"` | Fix tool parameter values |
| `resource` | `"memory"` / `"disk"` / `"resource"` | Reduce task scope or free resources |
| `execution` | (catch-all) | Check tool implementation |

---

#### `evaluate_plan`

```python
evaluate_plan(plan: Plan, results: List[TaskResult]) -> Evaluation
```

Evaluates the outcome of a complete plan execution.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `plan` | `Plan` | The executed plan |
| `results` | `List[TaskResult]` | Results from all tasks |

**Checks performed:**

- Overall success rate vs. `criteria.min_success_rate`
- Whether all tasks completed vs. `criteria.require_all_tasks_complete`
- Failure pattern detection (repeated error types, sequential failures)
- If `enable_llm_reflection=True`: LLM-generated improvement suggestions

**Returns:** `Evaluation` with `plan_id` set and aggregate issues/suggestions.

---

#### `learn_from_episode`

```python
learn_from_episode(episode: Episode) -> None
```

Analyzes a completed episode and stores any insights for future planning.

Currently logs insights to structured logs. Future versions will persist insights to long-term memory for use in the planning prompt.

---

## ReflectionCriteria

**Import:** `from laios.reflection.reflector import ReflectionCriteria`

Thresholds used by the `Reflector` to determine success vs. failure.

### Constructor

```python
ReflectionCriteria(
    min_success_rate: float = 0.8,
    max_execution_time_multiplier: float = 2.0,
    require_all_tasks_complete: bool = True,
    check_output_quality: bool = True,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_success_rate` | `float` | `0.8` | Minimum fraction of tasks that must succeed for the plan to be considered successful |
| `max_execution_time_multiplier` | `float` | `2.0` | If a task takes more than `N × expected_time`, flag as slow |
| `require_all_tasks_complete` | `bool` | `True` | Whether incomplete tasks are flagged as issues |
| `check_output_quality` | `bool` | `True` | Whether to inspect output content (e.g., empty responses) |

### `from_config`

```python
@classmethod
from_config(cls, config: Dict[str, Any]) -> ReflectionCriteria
```

Creates criteria from a config dictionary. Recognized keys: `min_success_rate`, `max_execution_time_multiplier`, `require_all_tasks_complete`, `check_output_quality`.

```python
criteria = ReflectionCriteria.from_config({
    "min_success_rate": 0.9,
    "require_all_tasks_complete": False,
})
```

---

## FailurePattern

**Import:** `from laios.reflection.reflector import FailurePattern`

Represents a detected pattern of repeated failures across tasks.

| Attribute | Type | Description |
|-----------|------|-------------|
| `pattern_type` | `str` | Category: `"repeated_errors"`, `"sequential_failures"`, `"low_success_rate"` |
| `description` | `str` | Human-readable description |
| `occurrences` | `int` | How many times the pattern was observed |
| `affected_tasks` | `List[str]` | Task IDs involved |
| `suggested_fix` | `Optional[str]` | Recommendation for resolving the pattern |
| `detected_at` | `datetime` | When the pattern was detected |

```python
pattern.to_dict() -> Dict[str, Any]
```

---

## Evaluation Object

See [`Evaluation` in the Core API](core.md#evaluation) for the full field reference.

```python
class Evaluation(BaseModel):
    task_id: Optional[str]      # Set for task evaluations
    plan_id: Optional[str]      # Set for plan evaluations
    success: bool
    confidence: float           # 0.0–1.0
    issues: List[str]           # Detected problems
    suggestions: List[str]      # Improvement suggestions
    should_replan: bool         # Whether replanning is recommended
```

---

## Configuration

```yaml
# config/default.yaml
agent:
  enable_reflection: true
  max_replanning_attempts: 2
```

Setting `enable_reflection: false` skips the Reflector entirely. No evaluation or replanning will occur on task failures.

---

## Usage Example

```python
from laios.reflection.reflector import Reflector, ReflectionCriteria
from laios.llm.providers.ollama import OllamaClient

llm = OllamaClient(model="llama2")
criteria = ReflectionCriteria(min_success_rate=0.9)
reflector = Reflector(llm_client=llm, criteria=criteria)

# Evaluate a single task result
evaluation = reflector.evaluate_task(task, result)
print(f"Success: {evaluation.success}")
print(f"Should replan: {evaluation.should_replan}")
print(f"Issues: {evaluation.issues}")
print(f"Suggestions: {evaluation.suggestions}")

# Evaluate a full plan
plan_eval = reflector.evaluate_plan(plan, results)
print(f"Plan success: {plan_eval.success}")
```
