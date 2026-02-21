"""
Example 03: Custom Tool Creation
=================================
Demonstrates:
  - Class-based BaseTool with custom _validate() and _execute()
  - create_simple_tool() factory for lightweight tools
  - ToolRegistry.execute_tool() and schema inspection
  - Error handling (invalid input path)

Requirements:
  - No LLM required — runs fully offline

Run:
  python examples/03_custom_tool.py
"""

import hashlib
from typing import Literal

from pydantic import Field, field_validator

from laios.tools.base import BaseTool, ToolCategory, ToolInput, ToolOutput, create_simple_tool
from laios.tools.registry import ToolRegistry


# ── Class-based Tool ──────────────────────────────────────────────────────────

class HashInput(ToolInput):
    text: str = Field(description="Text to hash")
    algorithm: Literal["sha256", "md5", "sha1"] = Field(
        default="sha256",
        description="Hashing algorithm to use",
    )

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty or whitespace-only")
        return v


class HashTool(BaseTool):
    name = "text.hash"
    description = "Compute a cryptographic hash of a string"
    category = ToolCategory.DATA
    input_model = HashInput
    required_permissions = set()

    def _validate(self, input_data: HashInput) -> None:
        """Extra validation: reject strings longer than 1 MB."""
        if len(input_data.text) > 1_000_000:
            raise ValueError("text exceeds 1 MB limit")

    def _execute(self, input_data: HashInput) -> dict:
        h = hashlib.new(input_data.algorithm, input_data.text.encode())
        return {
            "algorithm": input_data.algorithm,
            "digest": h.hexdigest(),
            "input_length": len(input_data.text),
        }


# ── Factory-based Tool ────────────────────────────────────────────────────────

def _reverse_text(text: str) -> dict:
    return {"reversed": text[::-1], "length": len(text)}


reverse_tool = create_simple_tool(
    name="text.reverse",
    description="Reverse a string",
    func=_reverse_text,
    parameters={"text": {"type": "string", "description": "Text to reverse", "required": True}},
)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== Custom Tool Example ===\n")

    # Build a registry and register both tools
    registry = ToolRegistry()
    registry.register_tool(HashTool)
    registry.register_tool(type(reverse_tool))  # create_simple_tool returns an instance

    # ── Schema inspection ──
    print("--- Registered Tools ---")
    for name in registry.list_tools():
        tool = registry.get_tool(name)
        schema = tool.get_schema()
        params = ", ".join(schema.get("parameters", {}).keys())
        print(f"  {name:25s} params=[{params}]")

    # ── HashTool: sha256 (default) ──
    print("\n--- HashTool: sha256 ---")
    result = registry.execute_tool("text.hash", text="Hello, LAIOS!")
    if result.success:
        print(f"  algorithm : {result.data['algorithm']}")
        print(f"  digest    : {result.data['digest']}")
        print(f"  length    : {result.data['input_length']} chars")

    # ── HashTool: md5 ──
    print("\n--- HashTool: md5 ---")
    result = registry.execute_tool("text.hash", text="Hello, LAIOS!", algorithm="md5")
    if result.success:
        print(f"  digest    : {result.data['digest']}")

    # ── HashTool: sha1 ──
    print("\n--- HashTool: sha1 ---")
    result = registry.execute_tool("text.hash", text="Hello, LAIOS!", algorithm="sha1")
    if result.success:
        print(f"  digest    : {result.data['digest']}")

    # ── ReverseTool ──
    print("\n--- ReverseTool ---")
    result = registry.execute_tool("text.reverse", text="The quick brown fox")
    if result.success:
        print(f"  reversed  : {result.data['reversed']}")
        print(f"  length    : {result.data['length']}")

    # ── Error path: empty text ──
    print("\n--- Error Path: empty text ---")
    result = registry.execute_tool("text.hash", text="   ")
    print(f"  success   : {result.success}")
    print(f"  error     : {result.error}")

    # ── Error path: unknown algorithm (Pydantic validation) ──
    print("\n--- Error Path: bad algorithm ---")
    result = registry.execute_tool("text.hash", text="hello", algorithm="crc32")
    print(f"  success   : {result.success}")
    print(f"  error     : {result.error}")

    print("\nDone.")


if __name__ == "__main__":
    main()
