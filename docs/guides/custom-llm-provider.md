# Adding a Custom LLM Provider

LAIOS ships with three providers (Ollama, OpenAI, Anthropic) and an `LLMRouter`. This guide shows how to implement your own `LLMClient` subclass for any other LLM backend.

**Prerequisites:** Familiarity with [LLM API Reference](../api/llm.md).

---

## When to Write a Custom Provider

- **Local model via non-Ollama API** — e.g., llama.cpp server, LM Studio, text-generation-webui
- **Enterprise endpoint** — internal Azure OpenAI deployment, AWS Bedrock, etc.
- **Custom authentication** — bearer tokens, mTLS, header injection
- **Special behavior** — custom retry logic, token counting, prompt templates

For OpenAI-compatible APIs (many local models expose this), the existing `OpenAIClient` may already work by setting `base_url`:

```python
from laios.llm.providers.openai import OpenAIClient
# Point at a local OpenAI-compatible server (e.g., LM Studio)
client = OpenAIClient(model="local-model", base_url="http://localhost:1234/v1")
```

Try this first before writing a custom provider.

---

## Implementing LLMClient

```python
from typing import Dict, Generator, List, Optional
from laios.llm.client import LLMClient, LLMMessage, LLMResponse


class MyProviderClient(LLMClient):
    """Custom LLM provider for MyProvider API."""

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str = "https://api.myprovider.com/v1",
        timeout: int = 60,
    ):
        super().__init__(model=model)
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> LLMResponse:
        import httpx

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", self.model),
            finish_reason=choice.get("finish_reason"),
            usage=data.get("usage"),
        )

    def generate_with_system(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> LLMResponse:
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_message),
        ]
        return self.generate(messages, temperature, max_tokens, **kwargs)
```

---

## Implementing Streaming (Optional)

Override `generate_stream()` for true token-by-token streaming:

```python
    def generate_stream(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> Generator[str, None, None]:
        import httpx

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        with httpx.Client(timeout=self.timeout) as client:
            with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.startswith("data: ") and not line.endswith("[DONE]"):
                        import json
                        chunk = json.loads(line[6:])
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta and delta["content"]:
                            yield delta["content"]
```

If you do not override `generate_stream()`, the default implementation calls `generate()` and yields the full response as a single chunk. This works but loses the streaming benefit.

---

## Injecting into AgentController

### Option A: Override the config (recommended)

Create a custom `Config` and provide the provider info — but LAIOS only supports `"ollama"`, `"openai"`, and `"anthropic"` by name. For a custom provider, use Option B.

### Option B: Replace `_llm_client` after initialization

```python
from laios.core.agent import AgentController
from laios.core.types import Config

config = Config()
agent = AgentController(config)

# Replace the LLM client
agent._llm_client = MyProviderClient(
    model="my-model-v2",
    api_key="your-api-key",
)

# Use the agent normally
session = agent.create_session(user_id="demo")
response = agent.process_message(session.id, "Hello!")
print(response)
```

> **Note:** This replaces the LLM client in `AgentController` but does not update the `Reflector` or `Planner`, which each hold their own reference to the LLM client (set during initialization). To replace them all, pass the custom client to `AgentController` before the subsystems are created — or reinitialize the subsystems manually.

---

## Using LLMRouter for Fallback

The cleanest way to use a custom provider is as part of an `LLMRouter`:

```python
from laios.llm.router import LLMRouter
from laios.llm.providers.ollama import OllamaClient

router = LLMRouter(
    providers=[
        MyProviderClient(model="my-model", api_key="key"),  # primary
        OllamaClient(model="llama2"),                        # fallback
    ],
    strategy="fallback",
)

agent._llm_client = router
```

If `MyProviderClient.generate()` raises any exception, the router automatically falls back to Ollama.

---

## Error Handling Conventions

- **Raise exceptions** from `generate()` on transient failures (network errors, rate limits, auth failures). The `LLMRouter` catches these and tries the next provider.
- **Do not return** `LLMResponse(content="")` on failure — raise instead so the router and circuit breaker can respond correctly.
- The `AgentController`'s `CircuitBreaker` opens after 5 consecutive failures. Once open, `process_message()` returns an error string without calling the LLM.

```python
def generate(self, messages, ...):
    try:
        resp = self._call_api(messages, ...)
        return LLMResponse(content=resp["content"], model=self.model)
    except httpx.TimeoutException:
        raise RuntimeError("MyProvider API timed out")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise RuntimeError("MyProvider rate limit exceeded")
        raise
```

---

## Testing Your Provider

```python
from laios.llm.client import LLMMessage

def test_my_provider():
    client = MyProviderClient(model="test-model", api_key="test-key")
    messages = [LLMMessage(role="user", content="Say 'hello' and nothing else.")]
    response = client.generate(messages, max_tokens=10)
    assert response.content
    assert response.model

def test_my_provider_stream():
    client = MyProviderClient(model="test-model", api_key="test-key")
    messages = [LLMMessage(role="user", content="Count to 3.")]
    chunks = list(client.generate_stream(messages, max_tokens=20))
    assert len(chunks) > 0
    full_text = "".join(chunks)
    assert full_text
```
