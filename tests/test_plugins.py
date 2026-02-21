"""
Tests for Phase 7: Plugin Architecture

Tests plugin lifecycle, events, dependency resolution, and hook dispatching.
"""

import pytest
from typing import Any, Dict, List, Optional

from laios.plugins.base import PluginBase, PluginContext, PluginMeta
from laios.plugins.events import EventBus, PLUGIN_LOADED, PLUGIN_UNLOADED
from laios.plugins.loader import PluginLoader, PluginDependencyError
from laios.plugins.registry import PluginRegistry
from laios.core.types import Config
from laios.tools.registry import ToolRegistry


# ============================================================================
# Test Fixtures - Concrete Plugin Implementations
# ============================================================================


class SamplePlugin(PluginBase):
    name = "sample_plugin"
    version = "1.0.0"
    description = "A sample test plugin"
    author = "Test Author"
    tags = ["test"]

    def __init__(self):
        super().__init__()
        self.load_called = False
        self.unload_called = False
        self.sessions_started: List[str] = []
        self.sessions_ended: List[str] = []
        self.tasks_before: List[str] = []
        self.tasks_after: List[str] = []
        self.messages: List[str] = []

    def on_load(self, context: PluginContext) -> None:
        self.load_called = True

    def on_unload(self) -> None:
        self.unload_called = True

    def on_session_start(self, session_id: str, user_id: str) -> None:
        self.sessions_started.append(session_id)

    def on_session_end(self, session_id: str) -> None:
        self.sessions_ended.append(session_id)

    def on_before_task(self, task_id: str, tool_name: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        self.tasks_before.append(task_id)
        return None

    def on_after_task(self, task_id: str, tool_name: str, success: bool, result: Any) -> None:
        self.tasks_after.append(task_id)

    def on_message(self, session_id: str, role: str, content: str) -> Optional[str]:
        self.messages.append(content)
        return None


class ParamModifyPlugin(PluginBase):
    """Plugin that modifies task parameters."""
    name = "param_modifier"
    version = "1.0.0"
    description = "Modifies task parameters"

    def on_load(self, context: PluginContext) -> None:
        pass

    def on_before_task(self, task_id: str, tool_name: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        modified = dict(parameters)
        modified["injected_by"] = "param_modifier"
        return modified


class DependentPluginA(PluginBase):
    name = "plugin_a"
    version = "1.0.0"
    description = "Plugin A (no deps)"
    dependencies = []

    def on_load(self, context: PluginContext) -> None:
        pass


class DependentPluginB(PluginBase):
    name = "plugin_b"
    version = "1.0.0"
    description = "Plugin B (depends on A)"
    dependencies = ["plugin_a"]

    def on_load(self, context: PluginContext) -> None:
        pass


class DependentPluginC(PluginBase):
    name = "plugin_c"
    version = "1.0.0"
    description = "Plugin C (depends on A and B)"
    dependencies = ["plugin_a", "plugin_b"]

    def on_load(self, context: PluginContext) -> None:
        pass


class CircularPluginX(PluginBase):
    name = "circular_x"
    version = "1.0.0"
    description = "Circular X"
    dependencies = ["circular_y"]

    def on_load(self, context: PluginContext) -> None:
        pass


class CircularPluginY(PluginBase):
    name = "circular_y"
    version = "1.0.0"
    description = "Circular Y"
    dependencies = ["circular_x"]

    def on_load(self, context: PluginContext) -> None:
        pass


@pytest.fixture
def tool_registry():
    return ToolRegistry()


@pytest.fixture
def config():
    return Config()


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def plugin_context(tool_registry, config, event_bus):
    return PluginContext(
        tool_registry=tool_registry,
        config=config,
        event_bus=event_bus,
    )


@pytest.fixture
def registry(event_bus):
    return PluginRegistry(event_bus=event_bus)


# ============================================================================
# Plugin Base Tests
# ============================================================================


class TestPluginBase:
    def test_plugin_creation(self):
        plugin = SamplePlugin()
        assert plugin.name == "sample_plugin"
        assert plugin.version == "1.0.0"
        assert not plugin._loaded
        assert plugin.enabled

    def test_plugin_load_unload(self, plugin_context):
        plugin = SamplePlugin()
        plugin.on_load(plugin_context)
        assert plugin.load_called

        plugin.on_unload()
        assert plugin.unload_called

    def test_plugin_get_info(self):
        plugin = SamplePlugin()
        info = plugin.get_info()
        assert info["name"] == "sample_plugin"
        assert info["version"] == "1.0.0"
        assert info["author"] == "Test Author"
        assert not info["loaded"]
        assert info["enabled"]
        assert "test" in info["tags"]

    def test_plugin_get_meta(self):
        plugin = SamplePlugin()
        meta = plugin.get_meta()
        assert isinstance(meta, PluginMeta)
        assert meta.name == "sample_plugin"
        meta_dict = meta.to_dict()
        assert meta_dict["name"] == "sample_plugin"

    def test_plugin_enable_disable(self):
        plugin = SamplePlugin()
        assert plugin.enabled
        plugin.enabled = False
        assert not plugin.enabled
        plugin.enabled = True
        assert plugin.enabled

    def test_plugin_repr(self):
        plugin = SamplePlugin()
        repr_str = repr(plugin)
        assert "sample_plugin" in repr_str
        assert "unloaded" in repr_str
        assert "enabled" in repr_str


# ============================================================================
# Plugin Lifecycle Hooks Tests
# ============================================================================


class TestPluginLifecycleHooks:
    def test_session_start_hook(self, plugin_context):
        plugin = SamplePlugin()
        plugin.on_load(plugin_context)
        plugin.on_session_start("session-1", "user-1")
        assert "session-1" in plugin.sessions_started

    def test_session_end_hook(self, plugin_context):
        plugin = SamplePlugin()
        plugin.on_load(plugin_context)
        plugin.on_session_end("session-1")
        assert "session-1" in plugin.sessions_ended

    def test_before_task_hook(self, plugin_context):
        plugin = SamplePlugin()
        plugin.on_load(plugin_context)
        result = plugin.on_before_task("task-1", "tool.x", {"key": "value"})
        assert result is None  # SamplePlugin returns None
        assert "task-1" in plugin.tasks_before

    def test_before_task_param_modification(self, plugin_context):
        plugin = ParamModifyPlugin()
        plugin.on_load(plugin_context)
        result = plugin.on_before_task("task-1", "tool.x", {"key": "value"})
        assert result is not None
        assert result["injected_by"] == "param_modifier"
        assert result["key"] == "value"

    def test_after_task_hook(self, plugin_context):
        plugin = SamplePlugin()
        plugin.on_load(plugin_context)
        plugin.on_after_task("task-1", "tool.x", True, "result_data")
        assert "task-1" in plugin.tasks_after

    def test_message_hook(self, plugin_context):
        plugin = SamplePlugin()
        plugin.on_load(plugin_context)
        result = plugin.on_message("session-1", "user", "hello")
        assert result is None
        assert "hello" in plugin.messages


# ============================================================================
# Event Bus Tests
# ============================================================================


class TestEventBus:
    def test_subscribe_and_emit(self):
        bus = EventBus()
        received = []
        bus.subscribe("test.event", lambda name, data: received.append(data))
        bus.emit("test.event", {"key": "value"})
        assert len(received) == 1
        assert received[0]["key"] == "value"

    def test_wildcard_subscription(self):
        bus = EventBus()
        received = []
        bus.subscribe("task.*", lambda name, data: received.append(name))
        bus.emit("task.started", {})
        bus.emit("task.completed", {})
        bus.emit("other.event", {})
        assert len(received) == 2
        assert "task.started" in received
        assert "task.completed" in received

    def test_global_wildcard(self):
        bus = EventBus()
        received = []
        bus.subscribe("*", lambda name, data: received.append(name))
        bus.emit("any.event", {})
        bus.emit("another.event", {})
        assert len(received) == 2

    def test_unsubscribe(self):
        bus = EventBus()
        received = []
        handler = lambda name, data: received.append(data)
        bus.subscribe("test.event", handler)
        bus.emit("test.event", {"n": 1})
        assert len(received) == 1

        bus.unsubscribe("test.event", handler)
        bus.emit("test.event", {"n": 2})
        assert len(received) == 1  # No new events

    def test_event_history(self):
        bus = EventBus()
        bus.emit("event.a", {"x": 1})
        bus.emit("event.b", {"x": 2})
        history = bus.get_history()
        assert len(history) == 2
        assert history[0]["name"] == "event.a"

    def test_event_history_filter(self):
        bus = EventBus()
        bus.emit("event.a", {})
        bus.emit("event.b", {})
        bus.emit("event.a", {})
        history = bus.get_history(event_name="event.a")
        assert len(history) == 2

    def test_event_history_limit(self):
        bus = EventBus(max_history=5)
        for i in range(10):
            bus.emit("event", {"i": i})
        history = bus.get_history()
        assert len(history) == 5

    def test_handler_error_isolation(self):
        bus = EventBus()
        received = []
        bus.subscribe("test", lambda name, data: 1 / 0)  # Will raise
        bus.subscribe("test", lambda name, data: received.append(True))
        bus.emit("test", {})
        assert len(received) == 1  # Second handler still called

    def test_subscriber_count(self):
        bus = EventBus()
        bus.subscribe("a", lambda n, d: None)
        bus.subscribe("a", lambda n, d: None)
        bus.subscribe("b", lambda n, d: None)
        assert bus.get_subscriber_count("a") == 2
        assert bus.get_subscriber_count("b") == 1
        assert bus.get_subscriber_count() == 3

    def test_clear_all(self):
        bus = EventBus()
        bus.subscribe("test", lambda n, d: None)
        bus.emit("test", {})
        bus.clear_all()
        assert bus.get_subscriber_count() == 0
        assert len(bus.get_history()) == 0


# ============================================================================
# Plugin Registry Tests
# ============================================================================


class TestPluginRegistry:
    def test_register_plugin(self, registry, plugin_context):
        plugin = SamplePlugin()
        plugin.on_load(plugin_context)
        plugin._loaded = True
        registry.register(plugin)
        assert "sample_plugin" in registry
        assert len(registry) == 1

    def test_unregister_plugin(self, registry, plugin_context):
        plugin = SamplePlugin()
        plugin.on_load(plugin_context)
        plugin._loaded = True
        registry.register(plugin)
        assert registry.unregister("sample_plugin")
        assert "sample_plugin" not in registry
        assert plugin.unload_called

    def test_enable_disable(self, registry, plugin_context):
        plugin = SamplePlugin()
        plugin.on_load(plugin_context)
        plugin._loaded = True
        registry.register(plugin)

        registry.disable_plugin("sample_plugin")
        assert not plugin.enabled

        registry.enable_plugin("sample_plugin")
        assert plugin.enabled

    def test_list_plugins_enabled_only(self, registry, plugin_context):
        p1 = SamplePlugin()
        p1.on_load(plugin_context)
        p1._loaded = True
        registry.register(p1)

        p2 = ParamModifyPlugin()
        p2.on_load(plugin_context)
        p2._loaded = True
        registry.register(p2)
        registry.disable_plugin("param_modifier")

        all_plugins = registry.list_plugins()
        assert len(all_plugins) == 2

        enabled_plugins = registry.list_plugins(enabled_only=True)
        assert len(enabled_plugins) == 1
        assert enabled_plugins[0].name == "sample_plugin"

    def test_dispatch_session_start(self, registry, plugin_context):
        plugin = SamplePlugin()
        plugin.on_load(plugin_context)
        plugin._loaded = True
        registry.register(plugin)

        registry.dispatch_session_start("sess-1", "user-1")
        assert "sess-1" in plugin.sessions_started

    def test_dispatch_session_end(self, registry, plugin_context):
        plugin = SamplePlugin()
        plugin.on_load(plugin_context)
        plugin._loaded = True
        registry.register(plugin)

        registry.dispatch_session_end("sess-1")
        assert "sess-1" in plugin.sessions_ended

    def test_dispatch_before_task_chaining(self, registry, plugin_context):
        """Test that parameter modifications chain through plugins."""
        p1 = ParamModifyPlugin()
        p1.on_load(plugin_context)
        p1._loaded = True
        registry.register(p1)

        result = registry.dispatch_before_task("task-1", "tool.x", {"key": "value"})
        assert result["injected_by"] == "param_modifier"
        assert result["key"] == "value"

    def test_dispatch_after_task(self, registry, plugin_context):
        plugin = SamplePlugin()
        plugin.on_load(plugin_context)
        plugin._loaded = True
        registry.register(plugin)

        registry.dispatch_after_task("task-1", "tool.x", True, "result")
        assert "task-1" in plugin.tasks_after

    def test_dispatch_message(self, registry, plugin_context):
        plugin = SamplePlugin()
        plugin.on_load(plugin_context)
        plugin._loaded = True
        registry.register(plugin)

        content = registry.dispatch_message("sess-1", "user", "hello")
        assert content == "hello"  # SamplePlugin returns None (no modification)
        assert "hello" in plugin.messages

    def test_disabled_plugins_skipped_in_hooks(self, registry, plugin_context):
        plugin = SamplePlugin()
        plugin.on_load(plugin_context)
        plugin._loaded = True
        registry.register(plugin)
        registry.disable_plugin("sample_plugin")

        registry.dispatch_session_start("sess-1", "user-1")
        assert len(plugin.sessions_started) == 0  # Should be skipped

    def test_event_emitted_on_register(self, event_bus):
        registry = PluginRegistry(event_bus=event_bus)
        received = []
        event_bus.subscribe(PLUGIN_LOADED, lambda n, d: received.append(d))

        plugin = SamplePlugin()
        plugin._loaded = True
        registry.register(plugin)
        assert len(received) == 1
        assert received[0]["name"] == "sample_plugin"

    def test_event_emitted_on_unregister(self, event_bus):
        registry = PluginRegistry(event_bus=event_bus)
        received = []
        event_bus.subscribe(PLUGIN_UNLOADED, lambda n, d: received.append(d))

        plugin = SamplePlugin()
        plugin._loaded = True
        registry.register(plugin)
        registry.unregister("sample_plugin")
        assert len(received) == 1
        assert received[0]["name"] == "sample_plugin"


# ============================================================================
# Plugin Dependency Resolution Tests
# ============================================================================


class TestPluginDependencyResolution:
    def test_no_dependencies(self):
        loader = PluginLoader()
        ordered = loader.resolve_load_order([DependentPluginA])
        assert len(ordered) == 1

    def test_simple_dependency_order(self):
        loader = PluginLoader()
        # B depends on A, so A should come first
        ordered = loader.resolve_load_order([DependentPluginB, DependentPluginA])
        names = [getattr(cls.__new__(cls), "name", cls.__name__) for cls in ordered]
        assert names.index("plugin_a") < names.index("plugin_b")

    def test_diamond_dependency_order(self):
        loader = PluginLoader()
        # C depends on A and B, B depends on A
        ordered = loader.resolve_load_order([
            DependentPluginC, DependentPluginB, DependentPluginA
        ])
        names = [getattr(cls.__new__(cls), "name", cls.__name__) for cls in ordered]
        assert names.index("plugin_a") < names.index("plugin_b")
        assert names.index("plugin_b") < names.index("plugin_c")

    def test_circular_dependency_detection(self):
        loader = PluginLoader()
        with pytest.raises(PluginDependencyError, match="Circular dependency"):
            loader.resolve_load_order([CircularPluginX, CircularPluginY])

    def test_missing_dependency_detection(self):
        loader = PluginLoader()
        # B depends on A, but A is not provided
        with pytest.raises(PluginDependencyError, match="missing plugins"):
            loader.resolve_load_order([DependentPluginB])


# ============================================================================
# Plugin Validation Tests
# ============================================================================


class TestPluginValidation:
    def test_validate_valid_plugin(self):
        loader = PluginLoader()
        errors = loader.validate_plugin(SamplePlugin)
        assert len(errors) == 0

    def test_validate_invalid_plugin(self):
        loader = PluginLoader()

        class BadPlugin(PluginBase):
            # name defaults to "base_plugin" - invalid
            def on_load(self, context):
                pass

        errors = loader.validate_plugin(BadPlugin)
        assert any("name" in e for e in errors)
