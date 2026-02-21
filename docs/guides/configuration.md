# Configuration Reference

LAIOS is configured via a YAML file. The default configuration is at `config/default.yaml`. You can override it with `--config path/to/config.yaml` on any CLI command, or load it programmatically with `Config.from_yaml("path/to/config.yaml")`.

---

## Loading Configuration

```python
from laios.core.types import Config

# From YAML file
config = Config.from_yaml("config/default.yaml")
config = Config.from_yaml("~/.laios/config.yaml")

# With all defaults (no file needed)
config = Config()

# Partial override in code
from laios.core.types import LLMConfig, AgentConfig, TrustLevel

config = Config(
    llm=LLMConfig(provider="openai", model="gpt-4o"),
    agent=AgentConfig(trust_level=TrustLevel.AUTONOMOUS),
)
```

**Validation:** `Config.from_yaml()` validates the YAML against the Pydantic schema. Unrecognized keys are silently ignored. Invalid values (e.g., wrong types, out-of-range numbers) raise a Pydantic `ValidationError`.

---

## Complete Annotated Config

Below is the full `config/default.yaml` with explanations for every key.

```yaml
# ── LLM Provider Settings ───────────────────────────────────────────────────
llm:
  provider: "ollama"        # Required. Options: "ollama", "openai", "anthropic"
  model: "gemma3:4b"        # Model name (provider-specific)
  base_url: "http://localhost:11434"  # Ollama server URL (ignored for OpenAI/Anthropic)
  temperature: 0.5          # Sampling randomness: 0.0 (deterministic) – 2.0 (creative)
  max_tokens: 2048          # Maximum tokens to generate per response
  timeout: 120              # HTTP request timeout in seconds
  keep_alive: "30m"         # How long Ollama keeps the model loaded (e.g., "5m", "1h", "-1" = forever)
  num_ctx: 4096             # Ollama context window size. Larger = more context, more RAM

# ── Agent Behavior ───────────────────────────────────────────────────────────
agent:
  trust_level: "balanced"   # See Trust Levels section below
  max_planning_iterations: 3   # Max LLM calls for plan refinement
  max_replanning_attempts: 2   # Max times to replan after task failure
  enable_reflection: true      # Whether to evaluate tasks/plans after execution

# ── Memory Configuration ─────────────────────────────────────────────────────
memory:
  short_term:
    max_messages: 50          # Max conversation messages before eviction (oldest removed)
    persist: true             # Persist session messages across restarts
    storage_path: "~/.laios/memory/sessions"

  long_term:
    enabled: true
    provider: "chromadb"      # Currently only chromadb supported
    storage_path: "~/.laios/memory/longterm"
    embedding_model: "all-MiniLM-L6-v2"
    max_results: 10           # Max results from long-term memory search

  episodic:
    enabled: true
    storage_path: "~/.laios/memory/episodes.db"
    retention_days: 90        # Episodes older than this are eligible for cleanup

# ── Tool Configuration ───────────────────────────────────────────────────────
tools:
  enabled:                    # Tool categories to load at startup
    - filesystem
    - shell
    - web
    - code

  permissions:
    filesystem:
      allowed_paths:          # Tools can only access these paths (and their subdirectories)
        - "~/"
        - "/tmp"
      denied_paths:           # These paths are blocked even if within allowed_paths
        - "/etc"
        - "/sys"
        - "~/.ssh"
      max_file_size_mb: 100   # Maximum file size for read/write operations

    shell:
      allowed_commands:       # Only these commands are permitted (empty list = all allowed)
        - "ls"
        - "cat"
        - "grep"
        - "find"
      deny_sudo: true         # Block commands containing "sudo"
      timeout: 30             # Shell command timeout in seconds

    web:
      max_request_size_mb: 10
      timeout: 30
      allowed_domains: []     # Empty = all domains allowed
      denied_domains:         # Block requests to these domains
        - "localhost"
        - "127.0.0.1"

# ── Execution Settings ───────────────────────────────────────────────────────
execution:
  mode: "sync"               # "sync" or "async"
  max_parallel_tasks: 5      # Max concurrent tasks in parallel execution
  task_timeout: 25           # Per-task timeout in seconds (overrides resource_limits)
  enable_sandboxing: false   # Reserved for future Docker/VM isolation

# ── Logging ──────────────────────────────────────────────────────────────────
logging:
  level: "INFO"              # DEBUG | INFO | WARNING | ERROR
  format: "structured"       # "structured" (JSON via structlog) or "plain" (human-readable)
  output: "console"          # "console", "file", or "both"
  file_path: "~/.laios/logs/laios.log"
  max_file_size_mb: 50
  backup_count: 5            # Number of rotated log files to keep

# ── UI Settings ──────────────────────────────────────────────────────────────
ui:
  cli:
    color: true              # Enable terminal color output
    rich_formatting: true    # Use Rich library for pretty output
    show_plan_before_execution: true  # Print the plan before executing

  api:
    host: "127.0.0.1"        # Bind address for the REST API server
    port: 8000
    enable_cors: false        # Enable CORS for browser clients
    allowed_origins: []       # Allowed CORS origins (requires enable_cors: true)

# ── Plugin Settings ──────────────────────────────────────────────────────────
plugins:
  enabled: true
  directories:               # Directories to scan for plugins (glob: */plugin.py)
    - "~/.laios/plugins"
    - "./plugins"
  auto_load: false           # If true, load plugins without explicit enable; if false, manual load

# ── Production Hardening ──────────────────────────────────────────────────────
hardening:
  circuit_breaker:
    failure_threshold: 5     # LLM call failures before opening the circuit
    recovery_timeout: 30     # Seconds before circuit attempts to close (half-open)

  rate_limiting:
    enabled: false
    rate: 10.0               # Allowed requests per second per API key
    capacity: 20             # Burst capacity
    global_rate: 50.0        # Global requests per second limit
    global_capacity: 100

  sanitization:
    max_input_length: 10000  # Maximum characters for user input messages
    max_path_length: 4096    # Maximum path length in tool parameters

  shutdown:
    timeout: 30              # Seconds to wait for in-flight tasks before forcing shutdown
```

---

## Trust Levels

The `agent.trust_level` controls how much autonomy the agent has when executing goals.

| Level | `execute_goal()` behavior | Use when |
|-------|--------------------------|----------|
| `paranoid` | Returns the plan with `awaiting_approval: True`. No tasks run. | You want to review and approve every plan before execution |
| `balanced` | Executes the plan automatically | Normal use (default) |
| `autonomous` | Executes everything, including destructive operations, without any confirmation | Automated pipelines where human confirmation is not possible |

**Note:** As of v1.0, the `balanced` level behaves the same as `autonomous` for standard tool execution. Future versions will add per-permission confirmation prompts.

---

## Memory Storage Paths

| Memory type | Default path |
|-------------|--------------|
| Short-term sessions | `~/.laios/memory/sessions/` |
| Long-term (ChromaDB) | `~/.laios/memory/longterm/` |
| Episodic (JSON files) | `~/.laios/memory/episodes/` |

**To clear all memory:**

```bash
rm -rf ~/.laios/memory/
```

---

## Plugin Directories

Plugins are auto-discovered from all directories listed under `plugins.directories`. Each subdirectory that contains a `plugin.py` file with a `PluginBase` subclass is treated as a plugin.

```yaml
plugins:
  directories:
    - "~/.laios/plugins"       # User-global plugins
    - "./my_project/plugins"   # Project-local plugins
```

---

## Logging Configuration

LAIOS uses [structlog](https://www.structlog.org/) for structured logging.

**Log levels:**

| Level | What is logged |
|-------|----------------|
| `DEBUG` | All internal events, tool invocations, LLM calls |
| `INFO` | Session lifecycle, task completions, configuration (default) |
| `WARNING` | Non-fatal issues, plugin validation warnings |
| `ERROR` | Failures, initialization errors |

**To enable debug logging:**

```yaml
logging:
  level: "DEBUG"
```

Or via CLI:

```bash
laios chat --verbose
```

---

## Environment Variables

For cloud LLM providers, set API keys in a `.env` file at the project root (loaded automatically by LAIOS):

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

These are not stored in the YAML config — they are read from the environment.

---

## Per-Session Config Override

You can create a session with a different configuration than the agent's default:

```python
from laios.core.types import Config, AgentConfig, TrustLevel

# Agent uses balanced trust by default
agent = AgentController(Config())

# But this session runs autonomously
autonomous_config = Config(agent=AgentConfig(trust_level=TrustLevel.AUTONOMOUS))
session = agent.create_session(user_id="bot", config=autonomous_config)
```
