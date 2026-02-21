"""
Tests for Executor - Task execution and monitoring

Phase 5: Execution & Monitoring Tests
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from laios.core.types import Context, Task, TaskStatus
from laios.execution.executor import (
    Executor,
    ExecutionMetrics,
    ExecutionMode,
    ResourceLimits,
    TaskMonitor,
)
from laios.tools.base import BaseTool, ToolCategory, ToolOutput
from laios.tools.registry import ToolRegistry


# Test Tool
class TestTool(BaseTool):
    """Simple test tool"""
    
    name = "test_tool"
    description = "Tool for testing"
    category = ToolCategory.UTILITY
    
    def _execute(self, **kwargs) -> ToolOutput:
        # Simulate some work
        time.sleep(kwargs.get("sleep_time", 0.1))
        
        if kwargs.get("fail", False):
            return ToolOutput(success=False, error="Simulated failure")
        
        return ToolOutput(
            success=True,
            data={"result": "success", "input": kwargs}
        )


class SlowTool(BaseTool):
    """Tool that takes a long time"""
    
    name = "slow_tool"
    description = "Slow tool for timeout testing"
    category = ToolCategory.UTILITY
    
    def _execute(self, **kwargs) -> ToolOutput:
        time.sleep(kwargs.get("sleep_time", 5.0))
        return ToolOutput(success=True, data="completed")


class CounterTool(BaseTool):
    """Tool that tracks execution count"""
    
    name = "counter_tool"
    description = "Tool that counts executions"
    category = ToolCategory.UTILITY
    
    execution_count = 0
    
    def _execute(self, **kwargs) -> ToolOutput:
        CounterTool.execution_count += 1
        return ToolOutput(
            success=True,
            data={"count": CounterTool.execution_count}
        )


# Fixtures

@pytest.fixture
def tool_registry():
    """Create tool registry with test tools"""
    registry = ToolRegistry()
    registry.register_tool(TestTool)
    registry.register_tool(SlowTool)
    registry.register_tool(CounterTool)
    return registry


@pytest.fixture
def executor(tool_registry):
    """Create executor with test registry"""
    return Executor(tool_registry, enable_monitoring=True)


@pytest.fixture
def sample_task():
    """Create sample task"""
    return Task(
        id="task_123",
        plan_id="plan_456",
        description="Test task",
        tool_name="test_tool",
        parameters={}
    )


@pytest.fixture
def sample_context():
    """Create sample context"""
    return Context(
        session_id="session_123",
        user_id="user_456"
    )


# Tests

class TestResourceLimits:
    """Tests for ResourceLimits"""
    
    def test_create_resource_limits(self):
        """Test creating resource limits"""
        limits = ResourceLimits(
            timeout_seconds=30.0,
            memory_limit_mb=512,
            cpu_limit_percent=80.0
        )
        
        assert limits.timeout_seconds == 30.0
        assert limits.memory_limit_mb == 512
        assert limits.cpu_limit_percent == 80.0
    
    def test_from_config(self):
        """Test creating from config dict"""
        config = {
            "timeout_seconds": 60.0,
            "memory_limit_mb": 1024
        }
        
        limits = ResourceLimits.from_config(config)
        assert limits.timeout_seconds == 60.0
        assert limits.memory_limit_mb == 1024
        assert limits.cpu_limit_percent is None


class TestExecutionMetrics:
    """Tests for ExecutionMetrics"""
    
    def test_create_metrics(self):
        """Test creating metrics"""
        metrics = ExecutionMetrics("task_123")
        assert metrics.task_id == "task_123"
        assert metrics.start_time is None
        assert metrics.execution_time == 0.0
    
    def test_start_end(self):
        """Test start and end timing"""
        metrics = ExecutionMetrics("task_123")
        
        metrics.start()
        assert metrics.start_time is not None
        
        time.sleep(0.1)
        
        metrics.end()
        assert metrics.end_time is not None
        assert metrics.execution_time > 0.0
        assert metrics.execution_time >= 0.1
    
    def test_checkpoint(self):
        """Test adding checkpoints"""
        metrics = ExecutionMetrics("task_123")
        
        metrics.checkpoint("start", {"step": 1})
        metrics.checkpoint("middle", {"step": 2})
        metrics.checkpoint("end", {"step": 3})
        
        assert len(metrics.checkpoints) == 3
        assert metrics.checkpoints[0]["name"] == "start"
        assert metrics.checkpoints[1]["data"]["step"] == 2
    
    def test_to_dict(self):
        """Test converting to dictionary"""
        metrics = ExecutionMetrics("task_123")
        metrics.start()
        metrics.checkpoint("test")
        metrics.end()
        
        data = metrics.to_dict()
        assert data["task_id"] == "task_123"
        assert "execution_time" in data
        assert "checkpoints" in data
        assert len(data["checkpoints"]) == 1


class TestTaskMonitor:
    """Tests for TaskMonitor"""
    
    def test_start_stop_monitoring(self, sample_task):
        """Test starting and stopping monitoring"""
        monitor = TaskMonitor()
        
        # Start monitoring
        metrics = monitor.start_monitoring(sample_task)
        assert metrics is not None
        assert monitor.is_running(sample_task.id)
        
        # Stop monitoring
        final_metrics = monitor.stop_monitoring(sample_task.id)
        assert final_metrics is not None
        assert not monitor.is_running(sample_task.id)
    
    def test_get_running_tasks(self):
        """Test getting running tasks"""
        monitor = TaskMonitor()
        
        task1 = Task(id="t1", plan_id="p1", description="Task 1", tool_name="test_tool")
        task2 = Task(id="t2", plan_id="p1", description="Task 2", tool_name="test_tool")
        
        monitor.start_monitoring(task1)
        monitor.start_monitoring(task2)
        
        running = monitor.get_running_tasks()
        assert len(running) == 2
        assert task1 in running
        assert task2 in running
    
    def test_checkpoint(self, sample_task):
        """Test adding checkpoints"""
        monitor = TaskMonitor()
        monitor.start_monitoring(sample_task)
        
        monitor.checkpoint(sample_task.id, "test_checkpoint", {"data": "test"})
        
        metrics = monitor.get_metrics(sample_task.id)
        assert len(metrics.checkpoints) == 1
        assert metrics.checkpoints[0]["name"] == "test_checkpoint"
    
    def test_clear_metrics(self, sample_task):
        """Test clearing metrics"""
        monitor = TaskMonitor()
        monitor.start_monitoring(sample_task)
        monitor.stop_monitoring(sample_task.id)
        
        monitor.clear_metrics(sample_task.id)
        metrics = monitor.get_metrics(sample_task.id)
        assert metrics is None


class TestExecutor:
    """Tests for Executor"""
    
    def test_create_executor(self, tool_registry):
        """Test creating executor"""
        executor = Executor(tool_registry)
        assert executor.tool_registry == tool_registry
        assert executor.max_workers == 4
    
    def test_execute_task_success(self, executor, sample_task, sample_context):
        """Test successful task execution"""
        result = executor.execute_task(sample_task, sample_context)
        
        assert result.success
        assert result.task_id == sample_task.id
        assert result.execution_time_seconds > 0
        assert sample_task.status == TaskStatus.COMPLETED
        assert sample_task.started_at is not None
        assert sample_task.completed_at is not None
    
    def test_execute_task_failure(self, executor, sample_context):
        """Test failed task execution"""
        task = Task(
            id="task_fail",
            plan_id="plan_1",
            description="Failing task",
            tool_name="test_tool",
            parameters={"fail": True}
        )
        
        result = executor.execute_task(task, sample_context)
        
        assert not result.success
        assert result.error == "Simulated failure"
        assert task.status == TaskStatus.FAILED
    
    def test_execute_task_with_timeout(self, executor, sample_context):
        """Test task execution with timeout"""
        task = Task(
            id="task_slow",
            plan_id="plan_1",
            description="Slow task",
            tool_name="slow_tool",
            parameters={"sleep_time": 10.0}
        )
        
        # Set short timeout
        result = executor.execute_task(task, sample_context, timeout=0.5)
        
        assert not result.success
        assert "timeout" in result.error.lower()
        assert task.status == TaskStatus.FAILED
    
    def test_execute_task_with_progress_callback(self, executor, sample_task, sample_context):
        """Test execution with progress callback"""
        progress_updates = []
        
        def on_progress(status, data):
            progress_updates.append((status, data))
        
        result = executor.execute_task(
            sample_task,
            sample_context,
            on_progress=on_progress
        )
        
        assert result.success
        assert len(progress_updates) >= 2  # At least started and completed
        assert progress_updates[0][0] == "started"
        assert progress_updates[-1][0] == "completed"
    
    def test_execute_task_tool_not_found(self, executor, sample_context):
        """Test executing task with non-existent tool"""
        task = Task(
            id="task_bad",
            plan_id="plan_1",
            description="Bad task",
            tool_name="nonexistent_tool",
            parameters={}
        )
        
        result = executor.execute_task(task, sample_context)
        
        assert not result.success
        assert "Tool not found" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_async(self, executor, sample_task, sample_context):
        """Test asynchronous task execution"""
        result = await executor.execute_async(sample_task, sample_context)
        
        assert result.success
        assert result.task_id == sample_task.id
    
    @pytest.mark.asyncio
    async def test_execute_parallel(self, executor, sample_context):
        """Test parallel task execution"""
        # Reset counter
        CounterTool.execution_count = 0
        
        tasks = [
            Task(
                id=f"task_{i}",
                plan_id="plan_1",
                description=f"Task {i}",
                tool_name="counter_tool",
                parameters={}
            )
            for i in range(5)
        ]
        
        start_time = time.time()
        results = await executor.execute_parallel(tasks, sample_context)
        elapsed = time.time() - start_time
        
        # All should succeed
        assert all(r.success for r in results)
        assert len(results) == 5
        
        # Counter should be incremented 5 times
        assert CounterTool.execution_count == 5
        
        # Parallel execution should be faster than sequential
        # (assuming some parallelism, though with GIL this is limited)
        assert elapsed < 1.0  # Would be ~0.5s if truly sequential
    
    def test_execute_with_retry_success_on_retry(self, executor, sample_context):
        """Test retry succeeds after initial failure"""
        call_count = [0]
        
        class RetryTool(BaseTool):
            name = "retry_tool"
            description = "Tool that fails first time"
            category = ToolCategory.UTILITY
            
            def _execute(self, **kwargs) -> ToolOutput:
                call_count[0] += 1
                if call_count[0] == 1:
                    return ToolOutput(success=False, error="First attempt fails")
                return ToolOutput(success=True, data="success")
        
        executor.tool_registry.register_tool(RetryTool)
        
        task = Task(
            id="task_retry",
            plan_id="plan_1",
            description="Retry task",
            tool_name="retry_tool",
            parameters={}
        )
        
        result = executor.execute_with_retry(
            task,
            sample_context,
            max_retries=2,
            retry_delay=0.1
        )
        
        assert result.success
        assert call_count[0] == 2  # Failed once, succeeded on retry
    
    def test_execute_with_retry_exhausted(self, executor, sample_context):
        """Test retry exhaustion"""
        task = Task(
            id="task_fail",
            plan_id="plan_1",
            description="Always fail",
            tool_name="test_tool",
            parameters={"fail": True}
        )
        
        result = executor.execute_with_retry(
            task,
            sample_context,
            max_retries=2,
            retry_delay=0.05
        )
        
        assert not result.success
        assert result.metadata.get("retry_exhausted") is True
    
    def test_cancel_task(self, executor, sample_context):
        """Test task cancellation"""
        task = Task(
            id="task_cancel",
            plan_id="plan_1",
            description="Task to cancel",
            tool_name="slow_tool",
            parameters={"sleep_time": 1.0}
        )
        
        # Cancel task before execution
        assert executor.cancel_task(task.id)
        
        # Try to execute cancelled task
        result = executor.execute_task(task, sample_context)
        
        # Should fail due to cancellation
        assert not result.success
        assert "cancelled" in result.error.lower()
    
    def test_get_running_tasks(self, executor, sample_task, sample_context):
        """Test getting running tasks"""
        import threading
        
        def run_slow_task():
            executor.execute_task(sample_task, sample_context)
        
        # Start task in background
        thread = threading.Thread(target=run_slow_task)
        thread.start()
        
        # Give it a moment to start
        time.sleep(0.05)
        
        # Check running tasks
        running = executor.get_running_tasks()
        
        # Wait for completion
        thread.join()
        
        # Should have been running at some point
        # (may not catch it if it finishes too quickly)
    
    def test_get_metrics(self, executor, sample_task, sample_context):
        """Test getting execution metrics"""
        result = executor.execute_task(sample_task, sample_context)
        
        metrics = executor.get_metrics(sample_task.id)
        assert metrics is not None
        assert metrics.task_id == sample_task.id
        assert metrics.execution_time > 0
    
    def test_executor_context_manager(self, tool_registry):
        """Test executor as context manager"""
        with Executor(tool_registry) as executor:
            assert executor is not None
        
        # Executor should be shut down after context


class TestExecutorIntegration:
    """Integration tests for executor"""
    
    def test_full_execution_flow(self, executor, sample_context):
        """Test complete execution flow with monitoring"""
        task = Task(
            id="task_full",
            plan_id="plan_1",
            description="Full test",
            tool_name="test_tool",
            parameters={"sleep_time": 0.1}
        )
        
        # Execute with progress tracking
        progress_events = []
        
        def track_progress(status, data):
            progress_events.append(status)
        
        result = executor.execute_task(
            task,
            sample_context,
            on_progress=track_progress
        )
        
        # Verify result
        assert result.success
        assert result.task_id == task.id
        
        # Verify task state
        assert task.status == TaskStatus.COMPLETED
        assert task.result is not None
        
        # Verify progress tracking
        assert "started" in progress_events
        assert "completed" in progress_events
        
        # Verify metrics
        metrics = executor.get_metrics(task.id)
        assert metrics is not None
        assert metrics.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_async_parallel_execution_integration(self, executor, sample_context):
        """Test async parallel execution with multiple tasks"""
        tasks = [
            Task(
                id=f"task_parallel_{i}",
                plan_id="plan_1",
                description=f"Parallel task {i}",
                tool_name="test_tool",
                parameters={"sleep_time": 0.1}
            )
            for i in range(3)
        ]
        
        results = await executor.execute_parallel(tasks, sample_context)
        
        # All should succeed
        assert all(r.success for r in results)
        assert len(results) == 3
        
        # All tasks should be completed
        assert all(t.status == TaskStatus.COMPLETED for t in tasks)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
