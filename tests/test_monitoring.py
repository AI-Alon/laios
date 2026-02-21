"""
Tests for Execution Monitoring

Tests for progress tracking, execution statistics, and performance monitoring.
"""

import time

import pytest

from laios.core.types import Task, TaskStatus
from laios.execution.monitor import (
    ExecutionMonitor,
    ExecutionStats,
    PerformanceMonitor,
    ProgressStatus,
    ProgressTracker,
    ProgressUpdate,
    get_execution_monitor,
    get_performance_monitor,
)


class TestProgressUpdate:
    """Tests for ProgressUpdate"""
    
    def test_create_progress_update(self):
        """Test creating progress update"""
        update = ProgressUpdate(
            task_id="task_123",
            status=ProgressStatus.IN_PROGRESS,
            progress_percent=50.0,
            message="Halfway done",
            details={"step": 5}
        )
        
        assert update.task_id == "task_123"
        assert update.status == ProgressStatus.IN_PROGRESS
        assert update.progress_percent == 50.0
        assert update.message == "Halfway done"
        assert update.details["step"] == 5


class TestProgressTracker:
    """Tests for ProgressTracker"""
    
    def test_update_progress(self):
        """Test updating progress"""
        tracker = ProgressTracker()
        
        tracker.update_progress(
            task_id="task_1",
            status=ProgressStatus.STARTING,
            progress_percent=0.0,
            message="Starting task"
        )
        
        progress = tracker.get_progress("task_1")
        assert progress is not None
        assert progress.status == ProgressStatus.STARTING
        assert progress.progress_percent == 0.0
    
    def test_progress_history(self):
        """Test progress history tracking"""
        tracker = ProgressTracker()
        
        # Add multiple updates
        tracker.update_progress("task_1", ProgressStatus.STARTING, 0.0)
        tracker.update_progress("task_1", ProgressStatus.IN_PROGRESS, 25.0)
        tracker.update_progress("task_1", ProgressStatus.IN_PROGRESS, 50.0)
        tracker.update_progress("task_1", ProgressStatus.COMPLETING, 90.0)
        tracker.update_progress("task_1", ProgressStatus.COMPLETED, 100.0)
        
        history = tracker.get_history("task_1")
        assert len(history) == 5
        assert history[0].status == ProgressStatus.STARTING
        assert history[-1].status == ProgressStatus.COMPLETED
        assert history[-1].progress_percent == 100.0
    
    def test_clear_progress(self):
        """Test clearing progress"""
        tracker = ProgressTracker()
        
        tracker.update_progress("task_1", ProgressStatus.IN_PROGRESS, 50.0)
        tracker.clear_progress("task_1")
        
        progress = tracker.get_progress("task_1")
        assert progress is None
        
        history = tracker.get_history("task_1")
        assert len(history) == 0
    
    def test_progress_listeners(self):
        """Test progress update listeners"""
        tracker = ProgressTracker()
        updates_received = []
        
        def listener(update: ProgressUpdate):
            updates_received.append(update)
        
        tracker.add_listener(listener)
        
        tracker.update_progress("task_1", ProgressStatus.STARTING, 0.0)
        tracker.update_progress("task_1", ProgressStatus.COMPLETED, 100.0)
        
        assert len(updates_received) == 2
        assert updates_received[0].status == ProgressStatus.STARTING
        assert updates_received[1].status == ProgressStatus.COMPLETED
    
    def test_remove_listener(self):
        """Test removing progress listener"""
        tracker = ProgressTracker()
        updates_received = []
        
        def listener(update: ProgressUpdate):
            updates_received.append(update)
        
        tracker.add_listener(listener)
        tracker.update_progress("task_1", ProgressStatus.STARTING, 0.0)
        
        tracker.remove_listener(listener)
        tracker.update_progress("task_1", ProgressStatus.COMPLETED, 100.0)
        
        # Should only receive first update
        assert len(updates_received) == 1


class TestExecutionStats:
    """Tests for ExecutionStats"""
    
    def test_default_stats(self):
        """Test default stats values"""
        stats = ExecutionStats()
        
        assert stats.total_tasks == 0
        assert stats.completed_tasks == 0
        assert stats.failed_tasks == 0
        assert stats.success_rate == 0.0


class TestExecutionMonitor:
    """Tests for ExecutionMonitor"""
    
    @pytest.fixture
    def monitor(self):
        """Create execution monitor"""
        return ExecutionMonitor()
    
    @pytest.fixture
    def sample_task(self):
        """Create sample task"""
        return Task(
            id="task_123",
            plan_id="plan_456",
            description="Test task",
            tool_name="test_tool",
            parameters={}
        )
    
    def test_start_task(self, monitor, sample_task):
        """Test starting task monitoring"""
        monitor.start_task(sample_task)
        
        progress = monitor.get_progress(sample_task.id)
        assert progress is not None
        assert progress.status == ProgressStatus.STARTING
    
    def test_update_task_progress(self, monitor, sample_task):
        """Test updating task progress"""
        monitor.start_task(sample_task)
        monitor.update_task_progress(
            sample_task.id,
            progress_percent=50.0,
            message="Halfway done"
        )
        
        progress = monitor.get_progress(sample_task.id)
        assert progress.status == ProgressStatus.IN_PROGRESS
        assert progress.progress_percent == 50.0
        assert progress.message == "Halfway done"
    
    def test_complete_task_success(self, monitor, sample_task):
        """Test completing task successfully"""
        monitor.start_task(sample_task)
        monitor.complete_task(sample_task, success=True)
        
        progress = monitor.get_progress(sample_task.id)
        assert progress.status == ProgressStatus.COMPLETED
        assert progress.progress_percent == 100.0
    
    def test_complete_task_failure(self, monitor, sample_task):
        """Test completing task with failure"""
        monitor.start_task(sample_task)
        monitor.complete_task(sample_task, success=False)
        
        progress = monitor.get_progress(sample_task.id)
        assert progress.status == ProgressStatus.FAILED
    
    def test_cancel_task(self, monitor, sample_task):
        """Test cancelling task"""
        monitor.start_task(sample_task)
        monitor.cancel_task(sample_task.id)
        
        progress = monitor.get_progress(sample_task.id)
        assert progress.status == ProgressStatus.CANCELLED
    
    def test_get_progress_history(self, monitor, sample_task):
        """Test getting progress history"""
        monitor.start_task(sample_task)
        monitor.update_task_progress(sample_task.id, 25.0)
        monitor.update_task_progress(sample_task.id, 50.0)
        monitor.complete_task(sample_task, success=True)
        
        history = monitor.get_progress_history(sample_task.id)
        assert len(history) >= 4  # start + 2 updates + complete
    
    def test_get_execution_stats(self, monitor):
        """Test calculating execution statistics"""
        from datetime import datetime, timedelta
        
        # Create tasks with different statuses
        tasks = []
        
        # Completed task
        task1 = Task(
            id="task_1",
            plan_id="plan_1",
            description="Task 1",
            tool_name="tool1",
            status=TaskStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow() + timedelta(seconds=1)
        )
        tasks.append(task1)
        
        # Failed task
        task2 = Task(
            id="task_2",
            plan_id="plan_1",
            description="Task 2",
            tool_name="tool2",
            status=TaskStatus.FAILED
        )
        tasks.append(task2)
        
        # Running task
        task3 = Task(
            id="task_3",
            plan_id="plan_1",
            description="Task 3",
            tool_name="tool3",
            status=TaskStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        tasks.append(task3)
        
        stats = monitor.get_execution_stats(tasks)
        
        assert stats.total_tasks == 3
        assert stats.completed_tasks == 1
        assert stats.failed_tasks == 1
        assert stats.running_tasks == 1
        assert stats.success_rate == 1/3  # 1 completed out of 3 total
    
    def test_add_remove_progress_listener(self, monitor, sample_task):
        """Test adding and removing progress listeners"""
        updates = []
        
        def listener(update):
            updates.append(update)
        
        monitor.add_progress_listener(listener)
        monitor.start_task(sample_task)
        
        assert len(updates) > 0
        
        monitor.remove_progress_listener(listener)
        monitor.update_task_progress(sample_task.id, 50.0)
        
        # Should still have only initial updates
        initial_count = len(updates)
        monitor.update_task_progress(sample_task.id, 75.0)
        assert len(updates) == initial_count
    
    def test_clear_task(self, monitor, sample_task):
        """Test clearing task monitoring data"""
        monitor.start_task(sample_task)
        monitor.clear_task(sample_task.id)
        
        progress = monitor.get_progress(sample_task.id)
        assert progress is None


class TestPerformanceMonitor:
    """Tests for PerformanceMonitor"""
    
    @pytest.fixture
    def perf_monitor(self):
        """Create performance monitor"""
        return PerformanceMonitor()
    
    def test_record_metric(self, perf_monitor):
        """Test recording performance metric"""
        perf_monitor.record_metric(
            task_id="task_1",
            metric_name="execution_time",
            value=1.5,
            unit="s"
        )
        
        metrics = perf_monitor.get_metrics("task_1")
        assert "execution_time" in metrics
        assert len(metrics["execution_time"]) == 1
        assert metrics["execution_time"][0]["value"] == 1.5
    
    def test_record_multiple_metrics(self, perf_monitor):
        """Test recording multiple metric values"""
        for i in range(5):
            perf_monitor.record_metric(
                task_id="task_1",
                metric_name="cpu_usage",
                value=50.0 + i * 5,
                unit="%"
            )
        
        metrics = perf_monitor.get_metrics("task_1")
        assert len(metrics["cpu_usage"]) == 5
    
    def test_get_metric_summary(self, perf_monitor):
        """Test getting metric summary statistics"""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        for value in values:
            perf_monitor.record_metric(
                task_id="task_1",
                metric_name="latency",
                value=value,
                unit="ms"
            )
        
        summary = perf_monitor.get_metric_summary("task_1", "latency")
        
        assert summary["min"] == 10.0
        assert summary["max"] == 50.0
        assert summary["avg"] == 30.0
        assert summary["count"] == 5
    
    def test_get_metric_summary_not_found(self, perf_monitor):
        """Test getting summary for non-existent metric"""
        summary = perf_monitor.get_metric_summary("task_1", "nonexistent")
        assert summary == {}
    
    def test_clear_metrics_single_task(self, perf_monitor):
        """Test clearing metrics for single task"""
        perf_monitor.record_metric("task_1", "metric1", 1.0)
        perf_monitor.record_metric("task_2", "metric2", 2.0)
        
        perf_monitor.clear_metrics("task_1")
        
        assert perf_monitor.get_metrics("task_1") == {}
        assert perf_monitor.get_metrics("task_2") != {}
    
    def test_clear_all_metrics(self, perf_monitor):
        """Test clearing all metrics"""
        perf_monitor.record_metric("task_1", "metric1", 1.0)
        perf_monitor.record_metric("task_2", "metric2", 2.0)
        
        perf_monitor.clear_metrics()
        
        assert perf_monitor.get_metrics("task_1") == {}
        assert perf_monitor.get_metrics("task_2") == {}


class TestGlobalMonitors:
    """Tests for global monitor instances"""
    
    def test_get_execution_monitor(self):
        """Test getting global execution monitor"""
        monitor1 = get_execution_monitor()
        monitor2 = get_execution_monitor()
        
        # Should return same instance
        assert monitor1 is monitor2
    
    def test_get_performance_monitor(self):
        """Test getting global performance monitor"""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        
        # Should return same instance
        assert monitor1 is monitor2


class TestMonitoringIntegration:
    """Integration tests for monitoring system"""
    
    def test_full_monitoring_flow(self):
        """Test complete monitoring flow"""
        monitor = ExecutionMonitor()
        perf_monitor = PerformanceMonitor()
        
        # Create task
        task = Task(
            id="task_integration",
            plan_id="plan_1",
            description="Integration test",
            tool_name="test_tool"
        )
        
        # Track progress updates
        progress_updates = []
        
        def track_updates(update):
            progress_updates.append(update.status)
        
        monitor.add_progress_listener(track_updates)
        
        # Simulate task execution
        monitor.start_task(task)
        
        # Record some metrics
        perf_monitor.record_metric(task.id, "cpu_usage", 45.0, "%")
        
        # Update progress
        monitor.update_task_progress(task.id, 25.0, "Loading data")
        perf_monitor.record_metric(task.id, "memory_usage", 128.0, "MB")
        
        monitor.update_task_progress(task.id, 50.0, "Processing")
        perf_monitor.record_metric(task.id, "cpu_usage", 75.0, "%")
        
        monitor.update_task_progress(task.id, 75.0, "Finalizing")
        perf_monitor.record_metric(task.id, "memory_usage", 256.0, "MB")
        
        # Complete task
        monitor.complete_task(task, success=True)
        
        # Verify progress tracking
        assert len(progress_updates) >= 4
        assert ProgressStatus.STARTING in progress_updates
        assert ProgressStatus.COMPLETED in progress_updates
        
        # Verify metrics
        metrics = perf_monitor.get_metrics(task.id)
        assert "cpu_usage" in metrics
        assert "memory_usage" in metrics
        
        # Verify summaries
        cpu_summary = perf_monitor.get_metric_summary(task.id, "cpu_usage")
        assert cpu_summary["min"] == 45.0
        assert cpu_summary["max"] == 75.0
        
        # Verify history
        history = monitor.get_progress_history(task.id)
        assert len(history) >= 5  # start + 3 updates + complete


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
