# LAIOS API Reference

Complete reference for all public classes, functions, and types in the `laios` package.

## Module Map

```
laios/
├── core/          → AgentController, Session, Config, Goal, Plan, Task, enums
├── tools/         → BaseTool, ToolRegistry, ToolInput, ToolOutput, create_simple_tool
├── llm/           → LLMClient, LLMMessage, LLMResponse, LLMRouter
│   └── providers/ → OllamaClient, OpenAIClient, AnthropicClient
├── memory/        → MemoryStore, Memory, Episode
├── planning/      → Planner
├── execution/     → Executor, ResourceLimits, ExecutionMetrics, TaskMonitor
├── reflection/    → Reflector, ReflectionCriteria, Evaluation
└── plugins/       → PluginBase, PluginContext, PluginRegistry, EventBus
```

## Top-Level Exports

```python
from laios import Config, Goal, Plan, Task, TaskStatus, PlanStatus
```

| Name | Type | Description |
|------|------|-------------|
| `Config` | class | Root configuration (LLM, agent, memory settings) |
| `Goal` | class | Structured user objective |
| `Plan` | class | DAG of executable tasks |
| `Task` | class | Single unit of work |
| `TaskStatus` | enum | `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`, `BLOCKED` |
| `PlanStatus` | enum | `DRAFT`, `APPROVED`, `EXECUTING`, `COMPLETED`, `FAILED`, `CANCELLED` |

## All Public Classes

| Class | Import Path | Description |
|-------|-------------|-------------|
| `AgentController` | `laios.core.agent` | Main orchestration entry point |
| `Session` | `laios.core.agent` | Active agent session |
| `Config` | `laios.core.types` | Root configuration model |
| `LLMConfig` | `laios.core.types` | LLM provider settings |
| `AgentConfig` | `laios.core.types` | Agent behavior settings |
| `MemoryConfig` | `laios.core.types` | Memory system settings |
| `Goal` | `laios.core.types` | User objective |
| `Plan` | `laios.core.types` | Execution plan (DAG) |
| `Task` | `laios.core.types` | Single executable unit |
| `TaskResult` | `laios.core.types` | Execution outcome |
| `Message` | `laios.core.types` | Conversation message |
| `Memory` | `laios.core.types` | Memory entry |
| `Episode` | `laios.core.types` | Completed goal execution record |
| `Evaluation` | `laios.core.types` | Reflection assessment |
| `Context` | `laios.core.types` | Shared execution context |
| `BaseTool` | `laios.tools.base` | Abstract base for all tools |
| `AsyncBaseTool` | `laios.tools.base` | Base for async tools |
| `ToolInput` | `laios.tools.base` | Base for tool input models |
| `ToolOutput` | `laios.tools.base` | Tool execution result |
| `ToolCategory` | `laios.tools.base` | Tool category enum |
| `ToolRegistry` | `laios.tools.registry` | Central tool store |
| `LLMClient` | `laios.llm.client` | Abstract LLM interface |
| `LLMMessage` | `laios.llm.client` | Chat message |
| `LLMResponse` | `laios.llm.client` | LLM response |
| `LLMRouter` | `laios.llm.router` | Multi-provider routing |
| `OllamaClient` | `laios.llm.providers.ollama` | Ollama provider |
| `OpenAIClient` | `laios.llm.providers.openai` | OpenAI provider |
| `AnthropicClient` | `laios.llm.providers.anthropic` | Anthropic provider |
| `MemoryStore` | `laios.memory.store` | Unified memory manager |
| `Planner` | `laios.planning.planner` | Goal-to-plan converter |
| `Executor` | `laios.execution.executor` | Task runner |
| `ResourceLimits` | `laios.execution.executor` | Execution constraints |
| `ExecutionMetrics` | `laios.execution.executor` | Per-task metrics |
| `TaskMonitor` | `laios.execution.executor` | Real-time task tracking |
| `Reflector` | `laios.reflection.reflector` | Self-evaluation engine |
| `ReflectionCriteria` | `laios.reflection.reflector` | Evaluation thresholds |
| `PluginBase` | `laios.plugins.base` | Abstract plugin base |
| `PluginContext` | `laios.plugins.base` | Plugin access to core systems |
| `PluginMeta` | `laios.plugins.base` | Plugin metadata |
| `PluginRegistry` | `laios.plugins.registry` | Plugin manager |
| `EventBus` | `laios.plugins.events` | Pub/sub event system |

## Import Conventions

```python
# High-level usage (most common)
from laios.core.agent import AgentController, Session
from laios.core.types import Config, Goal, Plan, Task, TaskResult
from laios.core.types import TaskStatus, PlanStatus, TrustLevel, Permission, MemoryType

# Tool development
from laios.tools.base import BaseTool, AsyncBaseTool, ToolInput, ToolOutput, ToolCategory
from laios.tools.base import create_simple_tool
from laios.tools.registry import ToolRegistry

# LLM clients
from laios.llm.client import LLMClient, LLMMessage, LLMResponse
from laios.llm.router import LLMRouter
from laios.llm.providers.ollama import OllamaClient
from laios.llm.providers.openai import OpenAIClient      # requires pip install 'laios[llm]'
from laios.llm.providers.anthropic import AnthropicClient # requires pip install 'laios[llm]'

# Memory
from laios.memory.store import MemoryStore

# Execution
from laios.execution.executor import Executor, ResourceLimits, ExecutionMetrics, TaskMonitor

# Plugins
from laios.plugins.base import PluginBase, PluginContext, PluginMeta
from laios.plugins.registry import PluginRegistry
from laios.plugins.events import EventBus, get_event_bus
```

## Versioning Policy

Current version: **0.1.0** (tracked in `laios/__init__.py`).

- Minor version bumps (`0.x.0`) may include breaking API changes during the pre-1.0 period.
- Patch version bumps (`0.0.x`) are backwards-compatible bug fixes.
- From v1.0.0 onwards: semantic versioning — breaking changes only in major versions.

## See Also

- [Core API](core.md) — `AgentController`, `Config`, types and enums
- [Tools API](tools.md) — `BaseTool`, `ToolRegistry`, built-in tools
- [LLM API](llm.md) — providers and routing
- [Memory API](memory.md) — `MemoryStore`
- [Planning API](planning.md) — `Planner`
- [Execution API](execution.md) — `Executor`, `ResourceLimits`
- [Reflection API](reflection.md) — `Reflector`
- [Plugins API](plugins.md) — `PluginBase`, `EventBus`
