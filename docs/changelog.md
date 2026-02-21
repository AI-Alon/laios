# Changelog

All notable changes to LAIOS are documented here.
This project follows [Semantic Versioning](https://semver.org/).

---

## v1.0.0 — 2026-02-19

### Added

**Phase 10 — Documentation & Examples (this release)**

- Full API reference for all public modules (`docs/api/`)
- Developer guides: creating tools, plugins, custom LLM providers, configuration (`docs/guides/`)
- Step-by-step tutorials (01–04) covering agents, memory, parallel execution, and plugins (`docs/tutorials/`)
- Six runnable example scripts in `examples/`
- MkDocs Material documentation site (`mkdocs.yml`)
- `docs/index.md` landing page with feature overview and "choose your path" table
- `docs/faq.md` with 15 common questions and answers
- `[docs]` optional dependency group in `pyproject.toml`

---

## Phase History

| Phase | Title | Status |
|-------|-------|--------|
| 0 | Project foundation, repo structure, `pyproject.toml`, CI skeleton | ✅ Complete |
| 1 | Core types (`Goal`, `Plan`, `Task`, `Config`, enums) and `AgentController` skeleton | ✅ Complete |
| 2 | Tool system — `BaseTool`, `ToolRegistry`, 15 built-in tools | ✅ Complete |
| 3 | LLM integration — `LLMClient`, `OllamaClient`, `OpenAIClient`, `AnthropicClient`, `LLMRouter` | ✅ Complete |
| 4 | Memory system — short-term, long-term, episodic; `MemoryStore` persistence | ✅ Complete |
| 5 | Planning engine — `Planner`, DAG decomposition, dependency resolution with NetworkX | ✅ Complete |
| 6 | Execution engine — `Executor`, sync/async/parallel modes, `ResourceLimits`, `TaskMonitor` | ✅ Complete |
| 7 | Reflection & replanning — `Reflector`, `ReflectionCriteria`, failure pattern detection | ✅ Complete |
| 8 | Plugin system — `PluginBase`, `PluginRegistry`, `EventBus`, lifecycle hooks | ✅ Complete |
| 9 | Web UI & REST API — FastAPI server, streaming endpoints, browser interface | ✅ Complete |
| 10 | Documentation & examples — API reference, guides, tutorials, example scripts, MkDocs site | ✅ Complete |

---

## Breaking Changes

None. This is the initial v1.0.0 release.

---

## Upgrade Notes

As this is the first stable release, no migration is required.
Future breaking changes will be listed here with migration instructions.
