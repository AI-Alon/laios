# LAIOS Architecture

## Overview

LAIOS (Local AI Operating System) is designed as a production-grade autonomous agent framework with clear separation of concerns and explicit state management.

## Design Principles

1. **Modularity** - Each subsystem has a single responsibility
2. **Explicit State** - No hidden prompts or magic behavior
3. **Local-First** - All data stays on user's machine
4. **Observable** - Full visibility into reasoning and execution
5. **Testable** - Components can be tested in isolation

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│  (CLI, API Server, WebUI - pluggable frontends)             │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    Agent Controller                          │
│  - Session management                                        │
│  - Request routing                                           │
│  - Lifecycle orchestration                                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│   Reasoner   │ │  Planner   │ │  Executor  │
└──────┬───────┘ └─────┬──────┘ └─────┬──────┘
       │               │               │
       └───────────────┼───────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
│ Memory Sys   │ │ Tool Reg │ │ Reflection │
└──────────────┘ └──────────┘ └────────────┘
```

## Component Responsibilities

### Agent Controller
- Central orchestration hub
- Manages session lifecycle
- Routes requests to appropriate subsystems
- Handles high-level error recovery

### Reasoner
- Parses natural language into structured goals
- Extracts entities, constraints, priorities
- Identifies ambiguities requiring clarification
- **Does not** make execution decisions

### Planner
- Decomposes goals into executable tasks
- Builds dependency graphs (DAGs)
- Validates plan feasibility
- Supports replanning on failure

### Executor
- Invokes tools to execute tasks
- Monitors execution progress
- Captures results and errors
- **Does not** contain planning logic

### Tool Registry
- Central catalog of available tools
- Schema validation for tool calls
- Permission enforcement
- Tool discovery for LLM

### Memory System
- **Short-term**: Conversation context
- **Long-term**: Vector embeddings for semantic search
- **Episodic**: Task history for learning

### Reflection Engine
- Evaluates task outcomes
- Detects failures and patterns
- Suggests improvements
- Triggers replanning when needed

## Data Flow

### Typical Request Flow

```
User Input
    ↓
Agent Controller
    ↓
Reasoner (parse intent)
    ↓
Planner (create task graph)
    ↓
Executor (execute tasks in topological order)
    ↓ (each task)
Tool Registry (validate + invoke)
    ↓
Task Result
    ↓
Reflection Engine (evaluate)
    ↓
Memory System (record episode)
    ↓
Response to User
```

## Technology Choices

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.10+ | Best LLM/ML ecosystem |
| Type System | Pydantic | Runtime validation |
| Graph Library | NetworkX | Standard DAG manipulation |
| Vector DB | ChromaDB | Pure Python, embedded |
| Storage | SQLite | Zero-config, ACID |
| Logging | structlog | Structured, queryable |
| CLI | Typer | Type-safe, modern |

## Key Design Decisions

### Why Explicit Plans?
Plans are first-class objects that can be:
- Inspected before execution
- Modified by users
- Saved and replayed
- Used for learning

### Why Separate Reasoner and Planner?
- **Single Responsibility**: Understanding intent ≠ task decomposition
- **Swappable**: Different LLMs or non-LLM approaches
- **Testable**: Mock one without the other

### Why Local-First?
- **Privacy**: Data never leaves user's machine
- **Cost**: No API fees
- **Reliability**: Works offline
- **Control**: No vendor lock-in

## Security Considerations

### Permission System
Every tool declares required permissions:
- `filesystem.read` / `filesystem.write`
- `shell.execute`
- `network.access`
- `code.execute`

### Sandboxing (Future)
- Docker containers for isolation
- Resource limits (CPU, memory, time)
- Network policies

### Trust Levels
- **Paranoid**: Confirm every action
- **Balanced**: Confirm risky operations
- **Autonomous**: Auto-execute safe operations

## Extensibility

### Plugin Architecture
Plugins are self-contained modules that:
- Register new tools
- Add custom planners
- Implement domain-specific logic
- Hot-loadable during development

### Tool Development
Tools are simple callables with schemas:
```python
def my_tool(param1: str, param2: int) -> dict:
    """Tool description"""
    return {"result": ...}

registry.register_tool(
    name="my_tool",
    description="Tool description",
    callable_func=my_tool,
    permissions={Permission.NETWORK_ACCESS}
)
```

## Future Enhancements

- Multi-agent collaboration
- Distributed execution
- Advanced planning (Monte Carlo Tree Search, etc.)
- Tool learning and optimization
- GUI workflow builder

## References

- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT)
- [LangChain Architecture](https://docs.langchain.com/docs/)
