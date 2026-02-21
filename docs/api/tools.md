# Tools API Reference

The `laios.tools` package provides the base classes for creating tools, the central `ToolRegistry`, and 15+ built-in tools across 6 categories.

---

## BaseTool

**Import:** `from laios.tools.base import BaseTool`

Abstract base class for all LAIOS tools. Tools are self-contained, permission-declaring, schema-generating units of functionality.

### Class Attributes (override in subclasses)

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | `"base_tool"` | **Required.** Unique tool identifier (e.g., `"filesystem.read_file"`) |
| `description` | `str` | `"Base tool class"` | **Required.** Human-readable description for LLM consumption |
| `category` | `ToolCategory` | `ToolCategory.CUSTOM` | Tool category for filtering |
| `required_permissions` | `set` | `set()` | Set of `Permission` values this tool requires |
| `input_model` | `Type[ToolInput]` | `ToolInput` | Pydantic model that validates input parameters |

### Constructor

```python
BaseTool()
```

Validates that `name`, `description`, and `input_model` are properly defined. Raises `ValueError` if `name` is still `"base_tool"` or `description` is empty.

### Methods

#### `execute`

```python
execute(**kwargs) -> ToolOutput
```

Main entry point for tool execution. Handles the full lifecycle:

1. Validates input via `validate_input(**kwargs)` → Pydantic model
2. Calls `_validate(validated_input)` for custom checks
3. Calls `_execute(validated_input)` for the tool's logic
4. Wraps the return value in `ToolOutput(success=True, data=result)` if it is not already a `ToolOutput`
5. Catches **all exceptions** and returns `ToolOutput(success=False, error=str(e), metadata={"error_type": ...})`

**Returns:** `ToolOutput` — never raises.

---

#### `_execute` (abstract)

```python
@abstractmethod
_execute(input_data: ToolInput) -> Any
```

**Must be implemented by subclasses.** Contains the tool's core logic.

**Returns:** Any value. If not a `ToolOutput`, it is automatically wrapped in `ToolOutput(success=True, data=result)`.

**Can raise:** Any exception — `execute()` catches it and returns a failure `ToolOutput`.

---

#### `_validate`

```python
_validate(input_data: ToolInput) -> None
```

Optional hook for custom cross-field validation. Called after Pydantic validation but before `_execute`.

**Override this** to add checks that Pydantic field validators cannot express (e.g., checking that a file path is within allowed directories, or that mutually exclusive fields are not both set).

**Raises:** `ValueError` with a descriptive message on failure.

---

#### `validate_input`

```python
validate_input(**kwargs) -> ToolInput
```

Creates and validates an instance of `input_model` from keyword arguments.

**Raises:** `pydantic.ValidationError` if input is invalid.

---

#### `get_parameters`

```python
get_parameters() -> List[ToolParameter]
```

Extracts parameter definitions from `input_model`'s JSON schema. Used for LLM tool discovery and schema export.

**Returns:** List of `ToolParameter` objects. Returns `[]` if `input_model == ToolInput` (no parameters).

---

#### `get_schema`

```python
get_schema() -> Dict[str, Any]
```

Returns the complete tool schema as a dictionary:

```python
{
    "name": "crypto.hash",
    "description": "Compute a cryptographic hash",
    "category": "custom",
    "parameters": [...],     # List of ToolParameter.model_dump()
    "permissions": [...]     # List of permission strings
}
```

---

### Minimal Example

```python
from pydantic import Field
from laios.tools.base import BaseTool, ToolCategory, ToolInput
from laios.core.types import Permission

class MyInput(ToolInput):
    text: str = Field(description="Text to process")
    upper: bool = Field(default=False, description="Convert to uppercase")

class MyTool(BaseTool):
    name = "text.transform"
    description = "Transforms text to upper or lower case"
    category = ToolCategory.CUSTOM
    input_model = MyInput
    required_permissions = set()

    def _validate(self, input_data: MyInput) -> None:
        if not input_data.text.strip():
            raise ValueError("text cannot be empty")

    def _execute(self, input_data: MyInput):
        return input_data.text.upper() if input_data.upper else input_data.text.lower()
```

---

## AsyncBaseTool

**Import:** `from laios.tools.base import AsyncBaseTool`

Subclass of `BaseTool` for tools that perform I/O or other async operations.

### Methods

#### `execute_async`

```python
async execute_async(**kwargs) -> ToolOutput
```

Async equivalent of `execute()`. Same lifecycle (validate → `_validate` → `_execute_async` → wrap). Catches all exceptions.

---

#### `_execute_async` (abstract)

```python
@abstractmethod
async _execute_async(input_data: ToolInput) -> Any
```

**Must be implemented.** Contains the async tool logic.

---

#### `_execute`

```python
_execute(input_data: ToolInput) -> Any
```

Raises `NotImplementedError`. Do not call `execute()` on async tools — use `execute_async()` instead.

---

### Async Example

```python
import httpx
from pydantic import Field
from laios.tools.base import AsyncBaseTool, ToolCategory, ToolInput

class FetchInput(ToolInput):
    url: str = Field(description="URL to fetch")

class AsyncFetchTool(AsyncBaseTool):
    name = "web.async_fetch"
    description = "Async HTTP GET request"
    category = ToolCategory.WEB
    input_model = FetchInput

    async def _execute_async(self, input_data: FetchInput):
        async with httpx.AsyncClient() as client:
            resp = await client.get(input_data.url, timeout=30)
            return {"status": resp.status_code, "body": resp.text[:1000]}
```

---

## ToolInput

**Import:** `from laios.tools.base import ToolInput`

Base Pydantic `BaseModel` for all tool input definitions. Subclass this to declare a tool's parameters.

```python
class ToolInput(BaseModel):
    pass  # no fields — override in subclass
```

**Usage:** Always use `Field(description="...")` on each field so the parameter appears in `get_schema()` output.

---

## ToolOutput

**Import:** `from laios.tools.base import ToolOutput`

Pydantic `BaseModel` representing a tool execution result.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `success` | `bool` | `True` | Whether the tool succeeded |
| `data` | `Any` | `None` | Output data (any JSON-serializable value) |
| `error` | `Optional[str]` | `None` | Error message (only set when `success=False`) |
| `metadata` | `Dict[str, Any]` | `{}` | Extra information (timing, error type, etc.) |

**Usage in `_execute`:**

```python
def _execute(self, input_data):
    if something_bad:
        return ToolOutput(success=False, error="Something went wrong")
    return ToolOutput(success=True, data={"result": 42})
    # OR just return the data directly:
    return {"result": 42}  # auto-wrapped in ToolOutput(success=True, data=...)
```

---

## ToolCategory

**Import:** `from laios.tools.base import ToolCategory`

```python
class ToolCategory(str, Enum):
    FILESYSTEM = "filesystem"
    SHELL      = "shell"
    WEB        = "web"
    CODE       = "code"
    DATA       = "data"
    SYSTEM     = "system"
    CUSTOM     = "custom"
```

---

## create_simple_tool

**Import:** `from laios.tools.base import create_simple_tool`

```python
create_simple_tool(
    name: str,
    description: str,
    func: callable,
    category: ToolCategory = ToolCategory.CUSTOM,
    permissions: Optional[set] = None,
    input_model: Optional[Type[ToolInput]] = None,
) -> BaseTool
```

Factory that creates a `BaseTool` instance from a plain Python function.

**How it works:** Creates a `SimpleTool` subclass dynamically. `_execute` calls `func(**input_data.model_dump())`. If no `input_model` is provided, any kwargs are accepted (no type enforcement).

**Returns:** A `BaseTool` instance (not a class). Register it by passing `type(tool)` to `ToolRegistry.register_tool()`, or use `registry.register_tools([type(tool)])`.

**Limitations:**
- No custom `_validate()` support
- No type-checked input parameters (unless you provide a custom `input_model`)
- Use for quick prototyping; prefer class-based tools in production

**Example:**

```python
from laios.tools.base import create_simple_tool

tool = create_simple_tool(
    name="text.reverse",
    description="Reverse a string",
    func=lambda text: text[::-1],
)

result = tool.execute(text="hello")
print(result.data)  # "olleh"
```

---

## ToolRegistry

**Import:** `from laios.tools.registry import ToolRegistry`

Central registry for tool discovery, validation, and execution. `AgentController` creates one automatically and pre-registers all built-in tools.

### Constructor

```python
ToolRegistry()
```

Creates an empty registry.

### Registration

#### `register_tool`

```python
register_tool(tool_class: Type[BaseTool]) -> None
```

Instantiates `tool_class()` and stores it by `tool.name`. If a tool with the same name already exists, logs a warning and replaces it.

**Example:**

```python
registry.register_tool(MyTool)
```

---

#### `register_tools`

```python
register_tools(tool_classes: List[Type[BaseTool]]) -> None
```

Registers a list of tool classes. Equivalent to calling `register_tool()` for each.

```python
from laios.tools.builtin import ALL_BUILTIN_TOOLS
registry.register_tools(ALL_BUILTIN_TOOLS)
```

---

### Lookup

#### `get_tool`

```python
get_tool(name: str) -> Optional[BaseTool]
```

Returns the tool instance for `name`, or `None` if not found.

---

#### `has_tool`

```python
has_tool(name: str) -> bool
```

Returns `True` if a tool with that name is registered.

---

#### `list_tools`

```python
list_tools(category: Optional[ToolCategory] = None,
           permission: Optional[Permission] = None) -> List[BaseTool]
```

Returns all registered tool instances, optionally filtered by category or required permission.

---

### Execution

#### `execute_tool`

```python
execute_tool(name: str, **kwargs) -> ToolOutput
```

Looks up the tool by name and calls `tool.execute(**kwargs)`.

**Raises:** `ValueError` if `name` is not registered. Otherwise returns `ToolOutput` (never raises from tool execution).

---

### Schema

#### `get_tool_schema`

```python
get_tool_schema(name: str) -> Optional[Dict[str, Any]]
```

Returns the schema dict for a tool, or `None` if not found.

---

#### `get_all_schemas`

```python
get_all_schemas() -> List[Dict[str, Any]]
```

Returns schema dicts for all registered tools. Used by the `Planner` for LLM tool discovery.

---

### Lifecycle

#### `unregister_tool`

```python
unregister_tool(name: str) -> bool
```

Removes a tool from the registry. Returns `True` if removed, `False` if not found.

---

#### `clear`

```python
clear() -> None
```

Removes all registered tools.

---

### Dunder Methods

```python
len(registry)          # Number of registered tools
"tool.name" in registry  # True if tool is registered
```

---

## Built-in Tool Groups

**Import:** `from laios.tools.builtin import ALL_BUILTIN_TOOLS`

| Import Name | Tools Included |
|-------------|----------------|
| `FILESYSTEM_TOOLS` | `filesystem.read_file`, `filesystem.write_file`, `filesystem.list_directory`, `filesystem.get_info` |
| `SHELL_TOOLS` | `shell.execute` |
| `WEB_TOOLS` | `web.fetch` |
| `GIT_TOOLS` | `git.status`, `git.log`, `git.diff`, `git.commit`, `git.clone` |
| `PYTHON_TOOLS` | `python.execute` |
| `DATA_TOOLS` | `data.parse_json`, `data.parse_csv`, `data.transform`, `data.format` |
| `ALL_BUILTIN_TOOLS` | All of the above |

### Filesystem Tools

| Tool Name | Description | Key Parameters |
|-----------|-------------|----------------|
| `filesystem.read_file` | Read text file contents | `path` (required), `encoding` (default: `"utf-8"`) |
| `filesystem.write_file` | Write content to file | `path`, `content` (required), `encoding`, `create_dirs` |
| `filesystem.list_directory` | List directory contents | `path`, `recursive`, `include_hidden`, `pattern` (glob) |
| `filesystem.get_info` | Get file/dir metadata | `path` (required) |

### Shell Tool

| Tool Name | Description | Key Parameters |
|-----------|-------------|----------------|
| `shell.execute` | Execute a shell command | `command` (required), `timeout` (max 300s), `working_dir` |

**Security:** Does not use `shell=True`. Blocks dangerous patterns: `rm -rf /`, `dd if=`, `mkfs`, `format`, fork bombs. Requires `SHELL_EXECUTE` permission.

### Web Tool

| Tool Name | Description | Key Parameters |
|-----------|-------------|----------------|
| `web.fetch` | HTTP/HTTPS request | `url` (required), `method` (`GET`/`POST`/etc.), `headers`, `body`, `timeout` |

### Git Tools

| Tool Name | Description | Key Parameters |
|-----------|-------------|----------------|
| `git.status` | Show working tree status | `path` |
| `git.log` | Show commit history | `path`, `count` (max 100), `oneline` |
| `git.diff` | Show file changes | `path`, `staged`, `file_path` |
| `git.commit` | Create a commit | `path`, `message` (required), `add_all` |
| `git.clone` | Clone a repository | `url` (required), `destination`, `depth` |

### Python Execution Tool

| Tool Name | Description | Key Parameters |
|-----------|-------------|----------------|
| `python.execute` | Run Python code in isolated subprocess | `code` (required), `timeout` (max 300s) |

### Data Tools

| Tool Name | Description | Key Parameters |
|-----------|-------------|----------------|
| `data.parse_json` | Parse JSON, extract by dot-path | `data` (required), `path` (e.g., `"users.0.name"`) |
| `data.parse_csv` | Parse CSV into records | `data` (required), `delimiter`, `has_header` |
| `data.transform` | Filter, sort, limit JSON arrays | `data`, `filter_key`, `filter_op`, `filter_value`, `sort_key`, `sort_reverse`, `limit` |
| `data.format` | Convert between JSON/CSV/YAML | `data`, `input_format`, `output_format` |

---

## ToolParameter

**Import:** `from laios.core.types import ToolParameter`

```python
class ToolParameter(BaseModel):
    name: str
    type: str          # "string", "number", "boolean", "object", "array"
    description: str
    required: bool = True
    default: Optional[Any] = None
    schema: Optional[Dict[str, Any]] = None  # JSON Schema fragment
```
