"""
Tests for tool registry
"""

import pytest

from laios.tools.registry import ToolRegistry
from laios.tools.base import BaseTool, ToolInput, ToolCategory
from laios.core.types import Permission


class DummyTool(BaseTool):
    """Dummy tool for testing"""
    name = "test.dummy"
    description = "A dummy tool"
    category = ToolCategory.CUSTOM
    
    def _execute(self, input_data: ToolInput):
        return "dummy output"


class TestToolRegistry:
    """Tests for ToolRegistry"""
    
    def test_register_tool(self):
        """Test registering a tool"""
        registry = ToolRegistry()
        registry.register_tool(DummyTool)
        
        assert len(registry) == 1
        assert registry.has_tool("test.dummy")
    
    def test_get_tool(self):
        """Test retrieving a tool"""
        registry = ToolRegistry()
        registry.register_tool(DummyTool)
        
        tool = registry.get_tool("test.dummy")
        assert tool is not None
        assert tool.name == "test.dummy"
    
    def test_list_tools(self):
        """Test listing all tools"""
        registry = ToolRegistry()
        registry.register_tool(DummyTool)
        
        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0].name == "test.dummy"
    
    def test_execute_tool(self):
        """Test executing a tool through registry"""
        registry = ToolRegistry()
        registry.register_tool(DummyTool)
        
        result = registry.execute_tool("test.dummy")
        assert result.success
        assert result.data == "dummy output"
    
    def test_execute_nonexistent_tool(self):
        """Test executing a tool that doesn't exist"""
        registry = ToolRegistry()
        
        result = registry.execute_tool("nonexistent.tool")
        assert not result.success
        assert "not found" in result.error.lower()
    
    def test_get_tool_schema(self):
        """Test getting tool schema"""
        registry = ToolRegistry()
        registry.register_tool(DummyTool)
        
        schema = registry.get_tool_schema("test.dummy")
        assert schema is not None
        assert schema["name"] == "test.dummy"
        assert "description" in schema
        assert "parameters" in schema
    
    def test_unregister_tool(self):
        """Test removing a tool"""
        registry = ToolRegistry()
        registry.register_tool(DummyTool)
        
        assert len(registry) == 1
        registry.unregister_tool("test.dummy")
        assert len(registry) == 0
    
    def test_clear_registry(self):
        """Test clearing all tools"""
        registry = ToolRegistry()
        registry.register_tool(DummyTool)
        
        registry.clear()
        assert len(registry) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
