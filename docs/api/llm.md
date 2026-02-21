# LLM API Reference

The `laios.llm` package provides a unified interface for LLM providers and multi-provider routing.

---

## LLMClient

**Import:** `from laios.llm.client import LLMClient`

Abstract base class that all LLM providers implement. Anywhere a `LLMClient` is accepted, any provider (or `LLMRouter`) can be used interchangeably.

### Constructor

```python
LLMClient(model: str, **kwargs)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `str` | Model name (stored as `self.model`) |

---

### Abstract Methods

#### `generate`

```python
@abstractmethod
generate(
    messages: List[LLMMessage],
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs,
) -> LLMResponse
```

Generates a response from the LLM.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `messages` | `List[LLMMessage]` | required | Conversation history |
| `temperature` | `float` | `0.7` | Sampling randomness (`0.0`–`2.0`) |
| `max_tokens` | `int` | `2048` | Maximum tokens to generate |

**Returns:** `LLMResponse`

**Raises:** Provider-specific exceptions on network failure, authentication error, etc. Callers (including `AgentController`) catch these.

---

#### `generate_with_system`

```python
@abstractmethod
generate_with_system(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs,
) -> LLMResponse
```

Convenience method that builds a two-message conversation (system + user) and calls `generate()`.

---

### Non-Abstract Methods

#### `generate_stream`

```python
generate_stream(
    messages: List[LLMMessage],
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs,
) -> Generator[str, None, None]
```

Yields text chunks as the LLM generates them.

**Default implementation:** Falls back to calling `generate()` and yielding the full response as a single chunk. Override in providers for true streaming.

**Usage:**

```python
for chunk in client.generate_stream(messages):
    print(chunk, end="", flush=True)
```

---

#### `count_tokens`

```python
count_tokens(text: str) -> int
```

Approximate token count (default: `len(text) // 4`). Override in provider subclasses for accurate counting.

---

## LLMMessage

**Import:** `from laios.llm.client import LLMMessage`

Pydantic `BaseModel` representing a single message in a conversation.

| Field | Type | Description |
|-------|------|-------------|
| `role` | `str` | `"system"`, `"user"`, or `"assistant"` |
| `content` | `str` | Message text |

**Usage:**

```python
from laios.llm.client import LLMMessage

messages = [
    LLMMessage(role="system", content="You are a helpful assistant."),
    LLMMessage(role="user", content="What is 2+2?"),
]
```

---

## LLMResponse

**Import:** `from laios.llm.client import LLMResponse`

Pydantic `BaseModel` returned by all `generate()` calls.

| Field | Type | Description |
|-------|------|-------------|
| `content` | `str` | Generated text |
| `model` | `str` | Model that generated the response |
| `finish_reason` | `Optional[str]` | Why generation stopped (e.g., `"stop"`, `"length"`) |
| `usage` | `Optional[Dict[str, int]]` | Token usage: `{"prompt_tokens": N, "completion_tokens": N, "total_tokens": N}` |
| `metadata` | `Dict` | Provider-specific extra data |

---

## OllamaClient

**Import:** `from laios.llm.providers.ollama import OllamaClient`

**Requires:** Ollama installed and running (`ollama serve`). Install the Python package: `pip install ollama`.

### Constructor

```python
OllamaClient(
    model: str,
    base_url: str = "http://localhost:11434",
    timeout: int = 60,
    keep_alive: str = "30m",
    num_ctx: Optional[int] = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | required | Model name (e.g., `"llama2"`, `"gemma3:4b"`) |
| `base_url` | `str` | `"http://localhost:11434"` | Ollama server URL |
| `timeout` | `int` | `60` | Request timeout in seconds |
| `keep_alive` | `str` | `"30m"` | How long to keep model loaded in memory |
| `num_ctx` | `Optional[int]` | `None` | Context window tokens (e.g., `4096`) |

**Streaming:** `generate_stream()` is fully implemented — yields tokens in real time.

**Usage:**

```python
from laios.llm.providers.ollama import OllamaClient
from laios.llm.client import LLMMessage

client = OllamaClient(model="llama2")
response = client.generate([LLMMessage(role="user", content="Hello!")])
print(response.content)
```

---

## OpenAIClient

**Import:** `from laios.llm.providers.openai import OpenAIClient`

**Requires:** `pip install 'laios[llm]'` and `OPENAI_API_KEY` environment variable.

### Constructor

```python
OpenAIClient(
    model: str,
    base_url: Optional[str] = None,
    timeout: int = 60,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | required | Model name (e.g., `"gpt-4o"`, `"gpt-3.5-turbo"`) |
| `base_url` | `Optional[str]` | `None` | Override for OpenAI-compatible endpoints (e.g., Azure OpenAI, local proxies) |
| `timeout` | `int` | `60` | Request timeout |

Reads `OPENAI_API_KEY` from the environment.

---

## AnthropicClient

**Import:** `from laios.llm.providers.anthropic import AnthropicClient`

**Requires:** `pip install 'laios[llm]'` and `ANTHROPIC_API_KEY` environment variable.

### Constructor

```python
AnthropicClient(
    model: str,
    timeout: int = 60,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | required | Model name (e.g., `"claude-sonnet-4-6"`) |
| `timeout` | `int` | `60` | Request timeout |

Reads `ANTHROPIC_API_KEY` from the environment.

---

## LLMRouter

**Import:** `from laios.llm.router import LLMRouter`

Routes LLM requests across multiple providers. Inherits from `LLMClient` — it can be used anywhere a `LLMClient` is accepted.

### Constructor

```python
LLMRouter(
    providers: List[LLMClient],
    strategy: str = "fallback",
    **kwargs,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `providers` | `List[LLMClient]` | required | Ordered list of provider clients (at least 1) |
| `strategy` | `str` | `"fallback"` | `"fallback"` or `"round_robin"` |

**Strategies:**

| Strategy | Behavior |
|----------|----------|
| `"fallback"` | Tries providers in list order. On exception, logs a warning and tries the next one. Raises `RuntimeError` if all fail. |
| `"round_robin"` | Distributes requests evenly using a rotating index. On exception, tries the next provider. Raises `RuntimeError` if all fail. |

**Note:** `LLMRouter.model` is set to `providers[0].model`.

**Raises:** `ValueError` if `providers` is an empty list.

---

### Methods

#### `generate`

```python
generate(
    messages: List[LLMMessage],
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs,
) -> LLMResponse
```

Routes to `_generate_fallback()` or `_generate_round_robin()` based on `self.strategy`.

---

#### `generate_with_system`

```python
generate_with_system(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs,
) -> LLMResponse
```

Builds a system + user message list and calls `generate()`.

---

#### `get_usage_stats`

```python
get_usage_stats() -> Dict[str, Dict[str, Any]]
```

Returns per-provider usage statistics since the router was created.

**Return structure:**

```python
{
    "OllamaClient(llama2)": {
        "calls": 10,
        "failures": 1,
        "total_tokens": 5000,
    },
    "OpenAIClient(gpt-3.5-turbo)": {
        "calls": 1,
        "failures": 0,
        "total_tokens": 200,
    },
}
```

Provider names are formatted as `ClassName(model)`.

---

### Usage Example

```python
from laios.llm.router import LLMRouter
from laios.llm.providers.ollama import OllamaClient
from laios.llm.providers.openai import OpenAIClient

router = LLMRouter(
    providers=[
        OllamaClient(model="llama2"),         # primary
        OpenAIClient(model="gpt-3.5-turbo"),  # fallback
    ],
    strategy="fallback",
)

response = router.generate([LLMMessage(role="user", content="Hello!")])
print(response.content)

stats = router.get_usage_stats()
for provider, s in stats.items():
    print(f"{provider}: calls={s['calls']}, failures={s['failures']}")
```

---

## Injecting a Custom LLM Client

`AgentController` exposes `_llm_client` as an instance variable. You can replace it after initialization:

```python
from laios.core.agent import AgentController
from laios.core.types import Config
from laios.llm.router import LLMRouter

config = Config()
agent = AgentController(config)

# Replace with a router
router = LLMRouter(providers=[...])
agent._llm_client = router
```

> **Note:** This bypasses the standard initialization path and should only be used in tests or scripts. For production use, configure the provider via `Config.llm.provider`.
