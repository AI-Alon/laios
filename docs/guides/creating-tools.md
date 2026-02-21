# Creating Custom Tools

Tools are the units of action in LAIOS — they are what the agent actually does. This guide walks through creating your own tools, from a minimal prototype to a production-ready implementation.

**Prerequisites:** Familiarity with [Tools API Reference](../api/tools.md).

---

## Tool Architecture

When a task is executed, the flow is:

```
ToolRegistry.execute_tool(name, **kwargs)
  └─> BaseTool.execute(**kwargs)
        ├─> validate_input(**kwargs)    ← Pydantic validation
        ├─> _validate(input_data)       ← Custom checks (override)
        └─> _execute(input_data)        ← Your logic (required)
              └─> ToolOutput(success=True, data=result)
```

All exceptions from `_validate` and `_execute` are caught by `execute()` and returned as `ToolOutput(success=False, error=...)`. Your `_execute` method will never bubble exceptions to the caller.

---

## Method 1: Class-Based Tool (Recommended)

This is the preferred approach for production tools. It gives you type-checked inputs, custom validation, schema generation, and testability.

### Step 1: Define Your Input Model

Create a Pydantic `ToolInput` subclass. Always include `Field(description="...")` on every field — these descriptions appear in the tool schema shown to the LLM.

```python
from pydantic import Field
from laios.tools.base import ToolInput

class WeatherInput(ToolInput):
    city: str = Field(description="City name to get weather for")
    units: str = Field(
        default="celsius",
        description="Temperature units: celsius or fahrenheit"
    )
```

### Step 2: Subclass BaseTool

```python
from laios.tools.base import BaseTool, ToolCategory, ToolOutput
from laios.core.types import Permission

class WeatherTool(BaseTool):
    name = "weather.get_current"
    description = "Get current weather conditions for a city"
    category = ToolCategory.WEB
    required_permissions = {Permission.NETWORK_ACCESS}
    input_model = WeatherInput

    def _validate(self, input_data: WeatherInput) -> None:
        if not input_data.city.strip():
            raise ValueError("city cannot be empty")
        if input_data.units not in ("celsius", "fahrenheit"):
            raise ValueError(f"Invalid units: {input_data.units}")

    def _execute(self, input_data: WeatherInput):
        # Replace with a real API call
        return {
            "city": input_data.city,
            "temperature": 22,
            "units": input_data.units,
            "conditions": "sunny",
        }
```

**Rules:**
- `name` must be unique — use dot notation like `"category.action"` (e.g., `"filesystem.read_file"`)
- `description` is shown to the LLM; make it clear and specific
- `required_permissions` declares what system resources the tool needs; empty set = no special permissions
- `_execute` can return any value — it is automatically wrapped in `ToolOutput(success=True, data=result)`
- To return a structured failure, return `ToolOutput(success=False, error="reason")` directly

### Step 3: Register with the Agent

```python
from laios.core.agent import AgentController
from laios.core.types import Config

config = Config()
agent = AgentController(config)
agent.get_tool_registry().register_tool(WeatherTool)
```

### Step 4: Test It

```python
tool = WeatherTool()

# Happy path
result = tool.execute(city="London", units="celsius")
assert result.success
assert result.data["city"] == "London"
print(result.data)  # {"city": "London", "temperature": 22, ...}

# Validation error (handled gracefully)
result = tool.execute(city="")
assert not result.success
assert "empty" in result.error

# Invalid units
result = tool.execute(city="Paris", units="kelvin")
assert not result.success
assert "Invalid units" in result.error
```

---

## Method 2: `create_simple_tool()` (Quick Prototyping)

For tools that wrap a simple function with no custom validation:

```python
from laios.tools.base import create_simple_tool

def reverse_text(text: str) -> str:
    return text[::-1]

reverse_tool = create_simple_tool(
    name="text.reverse",
    description="Reverse a string",
    func=reverse_text,
)

result = reverse_tool.execute(text="hello")
print(result.data)  # "olleh"
```

**Limitations:**
- No field-level type enforcement (any kwargs are accepted)
- No `_validate()` support
- The returned object is an instance, not a class — register via `type(reverse_tool)`

**When to use:** Rapid prototyping, one-off scripts, or wrapping third-party functions for experimentation. Switch to class-based for anything that will run in production.

---

## Handling Errors

Two patterns for signaling failure:

**Pattern 1: Raise an exception** (unexpected/unrecoverable errors)

```python
def _execute(self, input_data):
    if not Path(input_data.path).exists():
        raise FileNotFoundError(f"File not found: {input_data.path}")
    # ...
```

`execute()` catches this and returns `ToolOutput(success=False, error="File not found: ...")`.

**Pattern 2: Return a failure `ToolOutput`** (expected/recoverable failures)

```python
def _execute(self, input_data):
    response = requests.get(input_data.url, timeout=10)
    if response.status_code == 404:
        return ToolOutput(success=False, error=f"Resource not found: {input_data.url}")
    return {"status": response.status_code, "body": response.text}
```

Use Pattern 2 when the failure is an expected outcome (e.g., resource not found, rate limit hit). Both patterns produce the same `ToolOutput(success=False)` result.

---

## Async Tools

Use `AsyncBaseTool` for tools that perform I/O (HTTP requests, database queries, file operations on large files):

```python
import httpx
from laios.tools.base import AsyncBaseTool, ToolCategory, ToolInput
from pydantic import Field

class FetchInput(ToolInput):
    url: str = Field(description="URL to fetch")
    timeout: int = Field(default=30, description="Request timeout in seconds")

class AsyncFetchTool(AsyncBaseTool):
    name = "web.async_fetch"
    description = "Async HTTP GET request"
    category = ToolCategory.WEB
    input_model = FetchInput

    async def _execute_async(self, input_data: FetchInput):
        async with httpx.AsyncClient() as client:
            resp = await client.get(input_data.url, timeout=input_data.timeout)
            return {
                "status_code": resp.status_code,
                "body": resp.text[:5000],
                "headers": dict(resp.headers),
            }
```

**Usage:**

```python
tool = AsyncFetchTool()
import asyncio
result = asyncio.run(tool.execute_async(url="https://example.com"))
print(result.data["status_code"])
```

**Note:** Do not call `tool.execute()` on async tools — it raises `NotImplementedError`. Always use `execute_async()`.

---

## Declaring Permissions

Permissions help the agent enforce security policies based on `config.agent.trust_level`.

```python
from laios.core.types import Permission

class MyTool(BaseTool):
    required_permissions = {Permission.FILESYSTEM_WRITE, Permission.SHELL_EXECUTE}
```

Available permissions:

| Permission | When to use |
|-----------|-------------|
| `FILESYSTEM_READ` | Tool reads files from disk |
| `FILESYSTEM_WRITE` | Tool writes or deletes files |
| `SHELL_EXECUTE` | Tool runs shell commands |
| `NETWORK_ACCESS` | Tool makes HTTP/network requests |
| `CODE_EXECUTE` | Tool executes code (Python, etc.) |

Use `required_permissions = set()` if your tool does not need any system access (e.g., pure data transformation).

---

## Registering Tool Groups

For libraries or plugins that provide multiple tools:

```python
MY_TOOLS = [WeatherTool, AsyncFetchTool, AnotherTool]
registry.register_tools(MY_TOOLS)
```

Or in a plugin's `on_load()`:

```python
def on_load(self, context):
    context.tool_registry.register_tools(MY_TOOLS)
```

---

## Inspecting Tool Schema

```python
tool = WeatherTool()
schema = tool.get_schema()
print(schema)
# {
#   "name": "weather.get_current",
#   "description": "Get current weather conditions for a city",
#   "category": "web",
#   "parameters": [
#     {"name": "city", "type": "string", "description": "City name...", "required": True},
#     {"name": "units", "type": "string", "description": "Temperature units...", "required": False, "default": "celsius"},
#   ],
#   "permissions": ["network.access"]
# }
```

Via CLI:

```bash
laios tools describe weather.get_current
```

---

## Complete Working Example

Save this as `my_tools.py` and run `python my_tools.py`:

```python
import hashlib
from pydantic import Field
from laios.tools.base import BaseTool, ToolCategory, ToolInput
from laios.tools.registry import ToolRegistry
from laios.core.types import Permission


class HashInput(ToolInput):
    text: str = Field(description="Text to hash")
    algorithm: str = Field(
        default="sha256",
        description="Hash algorithm: md5, sha1, or sha256"
    )


class HashTool(BaseTool):
    name = "crypto.hash"
    description = "Compute a cryptographic hash of input text"
    category = ToolCategory.DATA
    input_model = HashInput
    required_permissions = set()

    def _validate(self, input_data: HashInput) -> None:
        if input_data.algorithm not in ("md5", "sha1", "sha256"):
            raise ValueError(f"Unsupported algorithm: {input_data.algorithm}")

    def _execute(self, input_data: HashInput):
        h = hashlib.new(input_data.algorithm)
        h.update(input_data.text.encode())
        return {"hash": h.hexdigest(), "algorithm": input_data.algorithm}


if __name__ == "__main__":
    registry = ToolRegistry()
    registry.register_tool(HashTool)

    result = registry.execute_tool("crypto.hash", text="hello world")
    print(f"SHA256: {result.data['hash']}")

    result = registry.execute_tool("crypto.hash", text="hello", algorithm="md5")
    print(f"MD5: {result.data['hash']}")

    result = registry.execute_tool("crypto.hash", text="test", algorithm="crc32")
    print(f"Error (expected): {result.error}")
```
