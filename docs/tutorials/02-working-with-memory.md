# Tutorial 2: Working with Memory

LAIOS provides three types of memory: short-term (in-memory conversation buffer), long-term (persistent JSON), and episodic (per-goal execution records). This tutorial shows how to use each tier and how the agent integrates memory into conversations.

**Time:** ~15 minutes
**Difficulty:** Beginner
**Prerequisite:** [Tutorial 1: Your First Agent](01-first-agent.md)

---

## Prerequisites

- LAIOS installed with `pip install -e ".[llm]"`
- Ollama running with `ollama serve` and a model pulled

---

## Step 1: Access the Memory Store

```python
from laios.core.agent import AgentController
from laios.core.types import Config

agent = AgentController(Config())
memory = agent.get_memory()

print(f"Memory store initialized.")
print(f"Long-term memories loaded: {len(memory.get_recent(n=100, memory_type=None))}")
```

---

## Step 2: Store a Long-Term Memory

Long-term memories persist to disk at `~/.laios/memory/long_term.json`. They survive agent restarts.

```python
# Store a fact about the user
mem1 = memory.store_long_term(
    "The user is a Python developer who prefers type hints and docstrings",
    metadata={"topic": "user_preferences", "source": "onboarding"},
)
print(f"Stored memory: {mem1.id[:8]}... (type={mem1.memory_type.value})")

mem2 = memory.store_long_term(
    "The project uses FastAPI for the REST API layer",
    metadata={"topic": "project_context"},
)
print(f"Stored memory: {mem2.id[:8]}...")
```

---

## Step 3: Search Memories

The `search()` method uses keyword scoring across both short-term and long-term memories.

```python
results = memory.search("python preferences", limit=5)
print(f"\nSearch results for 'python preferences': {len(results)}")

for m in results:
    print(f"  [{m.memory_type.value}] {m.content[:80]}")
    print(f"    metadata: {m.metadata}")
```

Try different queries:

```python
results = memory.search("FastAPI REST", limit=3)
print(f"\nSearch for 'FastAPI REST': {len(results)} results")
for m in results:
    print(f"  {m.content}")
```

---

## Step 4: Memory-Aware Conversations

`AgentController.process_message()` retrieves up to 3 relevant memories on the **first message** of a session and injects them into the system prompt. This means the agent "knows" what you stored before you even said anything.

```python
# Create a new session
session = agent.create_session(user_id="tutorial_user")

# First message — the agent will search memories and find our stored facts
response = agent.process_message(
    session.id,
    "What do you know about me and my project?"
)
print(f"\nAgent: {response}")
```

The agent should mention Python development preferences and FastAPI — because those are in long-term memory.

**How this works:** On the first message, `process_message()` calls `memory.search(user_message, limit=3)` and prepends the results to the system prompt as "Relevant context from memory".

---

## Step 5: Episode Memory — Execution Records

Every call to `execute_goal()` automatically stores an `Episode` — a complete record of the plan, tasks, and results.

```python
from laios.core.types import Goal

goal = Goal(description="List the Python files in the current directory")
result = agent.execute_goal(session.id, goal)

print(f"\nGoal executed. Episode: {result['episode_id'][:8]}...")
print(f"Success: {result['success']}")
```

Now retrieve the stored episode:

```python
# Get the most recent episodes
episodes = memory.get_episodes(limit=5)
print(f"\nStored episodes: {len(episodes)}")

for ep in episodes:
    print(f"  Episode {ep.id[:8]}:")
    print(f"    Goal: {ep.plan.goal.description}")
    print(f"    Tasks: {len(ep.plan.tasks)}")
    print(f"    Success: {ep.success}")
    print(f"    Created: {ep.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
```

Filter by session:

```python
session_episodes = memory.get_episodes(session_id=session.id, limit=10)
print(f"\nEpisodes for this session: {len(session_episodes)}")
```

---

## Step 6: Short-Term Memory

Short-term memory is the in-memory conversation buffer (default max: 50 messages). It is reset when the agent restarts.

```python
# Add a short-term memory
mem = memory.add(
    "User asked about code review workflows",
    metadata={"role": "observation", "session_id": session.id},
)
print(f"\nAdded short-term memory: {mem.id[:8]}...")

# Get recent short-term memories
from laios.core.types import MemoryType
recent = memory.get_recent(n=5, memory_type=MemoryType.SHORT_TERM)
print(f"Recent short-term memories: {len(recent)}")
for m in recent:
    print(f"  {m.content[:60]}")
```

---

## Step 7: Clearing Memory

```python
# Clear only short-term (long-term and episodic are unaffected)
memory.clear(MemoryType.SHORT_TERM)
print(f"\nShort-term memory cleared.")

# Clear all in-memory storage (does NOT delete disk files)
memory.clear()
print("All in-memory storage cleared.")
```

To permanently clear all memory (including disk):

```bash
rm -rf ~/.laios/memory/
```

---

## Storage Locations

| Tier | Default location |
|------|-----------------|
| Short-term | In-memory (lost on restart) |
| Long-term | `~/.laios/memory/long_term.json` |
| Episodic | `~/.laios/memory/episodes/<uuid>.json` |

---

## Complete Example Script

```python
from laios.core.agent import AgentController
from laios.core.types import Config, Goal, MemoryType

# Setup
agent = AgentController(Config())
memory = agent.get_memory()

# Pre-load knowledge
memory.store_long_term("User prefers concise output", metadata={"type": "pref"})
memory.store_long_term("Project is a LAIOS-based AI assistant", metadata={"type": "context"})

# Start a memory-aware conversation
session = agent.create_session(user_id="demo")
response = agent.process_message(session.id, "Summarize what you know about me.")
print(f"Response: {response}\n")

# Execute a goal and inspect the episode
result = agent.execute_goal(session.id, Goal(description="List Python files here"))
ep_id = result["episode_id"]
episode = memory.get_episode(ep_id)
if episode:
    print(f"Episode: {episode.id[:8]}, tasks={len(episode.plan.tasks)}, ok={episode.success}")

# Retrieve all stored memories
print("\nAll long-term memories:")
for m in memory.get_recent(n=10, memory_type=MemoryType.LONG_TERM):
    print(f"  - {m.content}")

agent.shutdown_session(session.id)
```

---

## Next Steps

- **[Tutorial 3: Parallel Execution](03-parallel-execution.md)** — run tasks concurrently
- **[Memory API Reference](../api/memory.md)** — complete API docs
