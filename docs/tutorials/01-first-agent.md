# Tutorial 1: Your First Agent

In this tutorial you will create an `AgentController`, start a session, send a chat message, and execute a structured goal — all from Python code. By the end you will understand the core pipeline and be ready to build on top of it.

**Time:** ~15 minutes
**Difficulty:** Beginner

---

## Prerequisites

- Python 3.10+
- LAIOS installed: `pip install -e ".[llm]"` from the LAIOS directory
- Ollama running: `ollama serve`
- Model pulled: `ollama pull llama2`

**Verify everything is ready:**

```bash
laios info
```

Expected output (approximately):

```
LAIOS v0.1.0
Provider:  ollama
Model:     llama2
Tools:     15 registered
Status:    ✓ LLM reachable
```

If the LLM status shows an error, check that `ollama serve` is running in another terminal.

---

## Step 1: Create the Agent

Create a file called `tutorial_01.py`:

```python
from laios.core.agent import AgentController
from laios.core.types import Config

# Config() uses all defaults: ollama / llama2 / balanced trust
config = Config()
agent = AgentController(config)

print("Agent initialized.")
print(f"Tools available: {len(agent.get_tool_registry())}")
```

Run it:

```bash
python tutorial_01.py
```

Expected output:

```
Agent initialized.
Tools available: 15
```

**What happened:** `AgentController` initialized the LLM client, loaded all 15 built-in tools into the `ToolRegistry`, started the memory store, and set up the plugin system.

---

## Step 2: Create a Session and Chat

Append to `tutorial_01.py`:

```python
# Create a session
session = agent.create_session(user_id="tutorial_user")
print(f"\nSession created: {session.id[:8]}...")

# Send a chat message
response = agent.process_message(session.id, "What tools do you have available?")
print(f"\nAgent: {response}")
```

Run again. The agent will call Ollama and return a response describing its capabilities.

**What happened:** `process_message()` added your message to the session, retrieved relevant memories (none yet, since this is the first message), called the LLM with a system prompt plus your message, and stored the response.

---

## Step 3: Execute a Structured Goal

Goals let the agent plan and execute multi-step tasks using its tools.

```python
from laios.core.types import Goal

goal = Goal(
    description="List all Python files in the current directory",
    priority=5,
)

print("\nExecuting goal...")
result = agent.execute_goal(session.id, goal)

print(f"Success: {result['success']}")
print(f"Tasks planned: {len(result['plan']['tasks'])}")
print(f"Tasks executed: {len(result['results'])}")
print(f"Episode stored: {result['episode_id'][:8]}...")

for task_result in result["results"]:
    status = "OK" if task_result["success"] else "FAIL"
    time = task_result["execution_time_seconds"]
    print(f"  [{status}] {task_result['task_id'][:8]} — {time:.2f}s")
    if task_result.get("output"):
        preview = str(task_result["output"])[:100]
        print(f"       Output: {preview}")
```

**What happened:** The `Planner` called the LLM to decompose your goal into tasks (e.g., `filesystem.list_directory`). The `Executor` ran each task in dependency order. The `Reflector` evaluated the results. An `Episode` was saved to `~/.laios/memory/episodes/`.

---

## Step 4: Inspect Session State

```python
state = agent.get_session_state(session.id)
print(f"\nSession state:")
print(f"  Messages: {state['message_count']}")
print(f"  LLM available: {state['llm_available']}")
print(f"  Reflection enabled: {state['reflection_enabled']}")
print(f"  Tools registered: {state['tools_registered']}")
```

---

## Step 5: Try Trust Levels

Trust levels control what the agent does when you call `execute_goal()`.

**PARANOID** — shows the plan but does not execute:

```python
from laios.core.types import Config, AgentConfig, TrustLevel

paranoid_config = Config(agent=AgentConfig(trust_level=TrustLevel.PARANOID))
paranoid_agent = AgentController(paranoid_config)
paranoid_session = paranoid_agent.create_session(user_id="reviewer")

goal = Goal(description="Create a file called test.txt with 'hello'")
result = paranoid_agent.execute_goal(paranoid_session.id, goal)

print(f"\nPARANOID mode:")
print(f"  awaiting_approval: {result.get('awaiting_approval')}")
print(f"  tasks executed: {len(result['results'])}")  # → 0
print(f"  plan has {len(result['plan']['tasks'])} tasks ready for review")
```

To execute, you would re-submit the goal with `TrustLevel.BALANCED` or `TrustLevel.AUTONOMOUS`.

**AUTONOMOUS** — executes everything without pausing:

```python
auto_config = Config(agent=AgentConfig(trust_level=TrustLevel.AUTONOMOUS))
auto_agent = AgentController(auto_config)
```

---

## Step 6: Clean Up

```python
# Close the session
agent.shutdown_session(session.id)
print("\nSession closed.")
```

---

## What Happened Under the Hood

```
You → process_message()
  → MemoryStore.add()           (stores your message)
  → MemoryStore.search()        (retrieves relevant memories, 1st message only)
  → LLMClient.generate()        (calls Ollama, wrapped in CircuitBreaker)
  → MemoryStore.add()           (stores response)
  → return response string

You → execute_goal()
  → Planner.create_plan()       (LLM decomposes goal into tasks)
  → EventBus.emit(PLAN_CREATED)
  → [for each ready task]
      → Executor.execute_task()  (invokes the tool)
      → EventBus.emit(TASK_COMPLETED or TASK_FAILED)
      → Reflector.evaluate_task() (on failure: should we replan?)
  → MemoryStore.store_episode()
  → Reflector.evaluate_plan()
  → return result dict
```

---

## Next Steps

- **[Tutorial 2: Working with Memory](02-working-with-memory.md)** — persist facts across sessions
- **[Tutorial 3: Parallel Execution](03-parallel-execution.md)** — run multiple tasks at once
- **[Tutorial 4: Building Plugins](04-building-plugins.md)** — extend the agent
- **[Examples](../../examples/README.md)** — runnable scripts for more use cases
