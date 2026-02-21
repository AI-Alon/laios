# Memory API Reference

The `laios.memory` package provides a three-tier memory system: short-term (in-memory), long-term (persistent JSON), and episodic (per-episode JSON files).

---

## MemoryStore

**Import:** `from laios.memory.store import MemoryStore`

Unified manager for all three memory tiers. `AgentController` creates one automatically; access it via `agent.get_memory()`.

### Constructor

```python
MemoryStore(
    config: Optional[MemoryConfig] = None,
    base_path: str = "~/.laios/memory",
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `Optional[MemoryConfig]` | `None` | Memory configuration |
| `base_path` | `str` | `"~/.laios/memory"` | Root directory for persistent storage |

**On initialization:**
- Creates `base_path/episodes/` and `base_path/long_term.json` if they don't exist
- Loads existing long-term memories from disk into memory

---

### Short-Term Memory

In-memory conversation buffer. Default maximum: 50 messages. Auto-evicts oldest entries when the limit is exceeded.

#### `add`

```python
add(
    content: str,
    memory_type: MemoryType = MemoryType.SHORT_TERM,
    metadata: Optional[Dict[str, Any]] = None,
) -> Memory
```

Adds a memory entry.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `str` | required | Text content to store |
| `memory_type` | `MemoryType` | `SHORT_TERM` | Which memory tier to use |
| `metadata` | `Optional[Dict]` | `None` | Arbitrary key-value metadata |

**Returns:** `Memory` object with the assigned `id`.

```python
mem = memory.add("User prefers Python 3.11", metadata={"source": "observation"})
print(mem.id)
```

---

#### `get_recent`

```python
get_recent(
    n: int = 10,
    memory_type: Optional[MemoryType] = None,
) -> List[Memory]
```

Returns the `n` most recent memory entries.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n` | `int` | `10` | Maximum number of entries to return |
| `memory_type` | `Optional[MemoryType]` | `None` | Filter by type; `None` returns all types |

```python
recent = memory.get_recent(n=5, memory_type=MemoryType.SHORT_TERM)
```

---

#### `clear`

```python
clear(memory_type: Optional[MemoryType] = None) -> None
```

Clears in-memory entries.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `memory_type` | `Optional[MemoryType]` | `None` | `None` clears all in-memory entries; specify a type to clear only that tier |

**Note:** Long-term memories stored to disk (`long_term.json`) and episodic files are **not** deleted by this method. They persist until the files are manually removed.

---

### Long-Term Memory

Persistent, keyword-searchable storage. Saved to `~/.laios/memory/long_term.json`.

#### `store_long_term`

```python
store_long_term(
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Memory
```

Persists a memory to disk and adds it to the in-memory long-term store.

```python
mem = memory.store_long_term(
    "The user prefers concise code with type hints",
    metadata={"topic": "preferences", "session": "session-123"},
)
```

---

#### `search`

```python
search(query: str, limit: int = 5) -> List[Memory]
```

Keyword-based search across both short-term and long-term memories. Uses simple word-overlap scoring — no vector embeddings required.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | required | Search query |
| `limit` | `int` | `5` | Maximum number of results |

**Returns:** List of `Memory` objects, most relevant first.

```python
results = memory.search("type hints python", limit=3)
for m in results:
    print(f"[{m.memory_type.value}] {m.content}")
```

---

### Episodic Memory

Persistent records of completed goal executions. Each episode is stored as a separate JSON file in `~/.laios/memory/episodes/<episode_id>.json`.

#### `store_episode`

```python
store_episode(episode: Episode) -> None
```

Saves an `Episode` to disk. Called automatically by `AgentController.execute_goal()`.

```python
from laios.core.types import Episode
memory.store_episode(episode)
```

---

#### `get_episode`

```python
get_episode(episode_id: str) -> Optional[Episode]
```

Retrieves a single episode by ID from disk.

```python
episode = memory.get_episode("abc123-...")
if episode:
    print(f"Tasks: {len(episode.plan.tasks)}, Success: {episode.success}")
```

---

#### `get_episodes`

```python
get_episodes(
    session_id: Optional[str] = None,
    limit: int = 10,
) -> List[Episode]
```

Retrieves stored episodes, sorted by creation time (newest first).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_id` | `Optional[str]` | `None` | Filter by session ID; `None` returns all sessions |
| `limit` | `int` | `10` | Maximum number of episodes to return |

```python
# All recent episodes
episodes = memory.get_episodes(limit=5)

# Episodes from a specific session
episodes = memory.get_episodes(session_id=session.id, limit=10)
```

---

## Storage Layout

```
~/.laios/memory/
├── long_term.json          # All long-term memories (JSON array)
└── episodes/
    ├── <uuid>.json         # One file per episode
    ├── <uuid>.json
    └── ...
```

**To clear all persistent memory:**

```bash
rm -rf ~/.laios/memory/
```

Or use the CLI:

```bash
laios memory list --type long_term
laios memory list --type episodic
```

---

## Memory Type Reference

| Tier | Class | Storage | Persistence | Search |
|------|-------|---------|-------------|--------|
| Short-term | `MemoryType.SHORT_TERM` | In-memory list | Lost on restart | Via `search()` |
| Long-term | `MemoryType.LONG_TERM` | `long_term.json` | Permanent | Via `search()` |
| Episodic | `MemoryType.EPISODIC` | `episodes/<id>.json` | Permanent | Via `get_episodes()` |

---

## Memory Object

See [`Memory` in the Core API](core.md#memory) for the full field reference.

**Key fields:**

```python
class Memory(BaseModel):
    id: str                          # UUID
    content: str                     # Stored text
    memory_type: MemoryType          # SHORT_TERM, LONG_TERM, or EPISODIC
    embedding: Optional[List[float]] # Vector embedding (future use)
    metadata: Dict[str, Any]         # Arbitrary key-values
    created_at: datetime
    accessed_at: datetime
```

---

## Episode Object

See [`Episode` in the Core API](core.md#episode) for the full field reference.

**Key fields:**

```python
class Episode(BaseModel):
    id: str                    # UUID
    session_id: str
    plan: Plan                 # The full plan that was executed
    results: List[TaskResult]  # One per task
    success: bool              # True if all tasks succeeded
    created_at: datetime
    metadata: Dict[str, Any]
```
