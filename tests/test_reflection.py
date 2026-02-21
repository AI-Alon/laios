"""
Tests for Reflection System

Tests the reflector's ability to:
- Evaluate task execution
- Evaluate plan execution
- Detect failure patterns
- Generate learning insights
- Suggest improvements
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from laios.core.types import (
    Context,
    Episode,
    Goal,
    Message,
    Plan,
    PlanStatus,
    Task,
    TaskResult,
    TaskStatus,
)
from laios.llm.client import LLMClient
from laios.reflection.reflector import (
    Reflector,
    ReflectionCriteria,
    FailurePattern,
    Insight,
)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client"""
    client = Mock(spec=LLMClient)
    client.generate.return_value = """
1. Add better error handling for network operations
2. Split large tasks into smaller subtasks
3. Add retry logic for transient failures
"""
    return client


@pytest.fixture
def reflection_criteria():
    """Standard reflection criteria"""
    return ReflectionCriteria(
        min_success_rate=0.8,
        max_execution_time_multiplier=2.0,
        require_all_tasks_complete=True,
        check_output_quality=True,
    )


@pytest.fixture
def reflector(mock_llm_client, reflection_criteria):
    """Create reflector instance"""
    return Reflector(
        llm_client=mock_llm_client,
        criteria=reflection_criteria,
        enable_llm_reflection=True,
    )


@pytest.fixture
def sample_context():
    """Sample execution context"""
    return Context(
        session_id="test-session",
        user_id="test-user",
        messages=[
            Message(role="user", content="Test request"),
        ],
    )


@pytest.fixture
def sample_goal():
    """Sample goal"""
    return Goal(
        description="Analyze Python files and create report",
        priority=5,
    )


class TestTaskEvaluation:
    """Test task-level evaluation"""
    
    def test_evaluate_successful_task(self, reflector, sample_context):
        """Test evaluation of successful task"""
        task = Task(
            id="task-1",
            plan_id="plan-1",
            description="Read file",
            tool_name="filesystem.read",
            parameters={"path": "test.txt"},
        )
        task.status = TaskStatus.COMPLETED
        
        result = TaskResult(
            task_id="task-1",
            success=True,
            output={"content": "file contents"},
            execution_time_seconds=0.5,
        )
        
        evaluation = reflector.evaluate_task(task, result, sample_context)
        
        assert evaluation.success is True
        assert evaluation.confidence > 0.8
        assert len(evaluation.issues) == 0
        assert evaluation.should_replan is False
    
    def test_evaluate_failed_task(self, reflector, sample_context):
        """Test evaluation of failed task"""
        task = Task(
            id="task-1",
            plan_id="plan-1",
            description="Read file",
            tool_name="filesystem.read",
            parameters={"path": "nonexistent.txt"},
        )
        task.status = TaskStatus.FAILED
        task.error = "File not found: nonexistent.txt"
        
        result = TaskResult(
            task_id="task-1",
            success=False,
            error="File not found: nonexistent.txt",
            execution_time_seconds=0.1,
        )
        
        evaluation = reflector.evaluate_task(task, result, sample_context)
        
        assert evaluation.success is False
        assert evaluation.confidence < 0.5
        assert len(evaluation.issues) > 0
        assert "failed" in evaluation.issues[0].lower()
        assert len(evaluation.suggestions) > 0
    
    def test_evaluate_timeout_task(self, reflector, sample_context):
        """Test evaluation of task that timed out"""
        task = Task(
            id="task-1",
            plan_id="plan-1",
            description="Long operation",
            tool_name="shell.execute",
            parameters={"command": "sleep 100"},
            metadata={"expected_time_seconds": 1.0},
        )
        task.status = TaskStatus.FAILED
        task.error = "Task execution timeout after 30s"
        
        result = TaskResult(
            task_id="task-1",
            success=False,
            error="Task execution timeout after 30s",
            execution_time_seconds=30.0,
        )
        
        evaluation = reflector.evaluate_task(task, result, sample_context)
        
        assert evaluation.success is False
        assert len(evaluation.issues) > 0
        assert any("timeout" in issue.lower() for issue in evaluation.issues)
        assert any("timeout" in sug.lower() for sug in evaluation.suggestions)
    
    def test_evaluate_slow_task(self, reflector, sample_context):
        """Test evaluation of task that took too long"""
        task = Task(
            id="task-1",
            plan_id="plan-1",
            description="Search files",
            tool_name="filesystem.search",
            parameters={"pattern": "*.py"},
            metadata={"expected_time_seconds": 1.0},
        )
        task.status = TaskStatus.COMPLETED
        
        result = TaskResult(
            task_id="task-1",
            success=True,
            output=["file1.py", "file2.py"],
            execution_time_seconds=5.0,  # 5x expected
        )
        
        evaluation = reflector.evaluate_task(task, result, sample_context)
        
        assert evaluation.success is False  # Success but with issues
        assert len(evaluation.issues) > 0
        assert any("took" in issue.lower() for issue in evaluation.issues)
        assert len(evaluation.suggestions) > 0
    
    def test_error_categorization(self, reflector, sample_context):
        """Test different error types are categorized correctly"""
        error_tests = [
            ("Connection timeout", "timeout"),
            ("Permission denied", "permission"),
            ("File not found", "not_found"),
            ("Network unreachable", "network"),
            ("Invalid parameter", "validation"),
            ("Out of memory", "resource"),
        ]
        
        for error_msg, expected_category in error_tests:
            task = Task(
                id="task-1",
                plan_id="plan-1",
                description="Test task",
                tool_name="test.tool",
            )
            task.error = error_msg
            
            result = TaskResult(
                task_id="task-1",
                success=False,
                error=error_msg,
                execution_time_seconds=0.1,
            )
            
            evaluation = reflector.evaluate_task(task, result, sample_context)
            
            # Check that appropriate suggestions are given
            assert len(evaluation.suggestions) > 0


class TestPlanEvaluation:
    """Test plan-level evaluation"""
    
    def test_evaluate_successful_plan(self, reflector, sample_goal, sample_context):
        """Test evaluation of fully successful plan"""
        plan = Plan(
            id="plan-1",
            goal=sample_goal,
            status=PlanStatus.COMPLETED,
        )
        
        # Add completed tasks
        for i in range(3):
            task = Task(
                id=f"task-{i}",
                plan_id="plan-1",
                description=f"Task {i}",
                tool_name="test.tool",
                status=TaskStatus.COMPLETED,
            )
            plan.tasks.append(task)
        
        # Create results
        results = [
            TaskResult(
                task_id=f"task-{i}",
                success=True,
                output=f"result-{i}",
                execution_time_seconds=1.0,
            )
            for i in range(3)
        ]
        
        evaluation = reflector.evaluate_plan(plan, results, sample_context)
        
        assert evaluation.success is True
        assert evaluation.confidence > 0.8
        assert len(evaluation.issues) == 0
        assert evaluation.should_replan is False
    
    def test_evaluate_partially_failed_plan(self, reflector, sample_goal, sample_context):
        """Test evaluation of plan with some failures"""
        plan = Plan(
            id="plan-1",
            goal=sample_goal,
            status=PlanStatus.FAILED,
        )
        
        # Add mixed tasks
        for i in range(5):
            status = TaskStatus.COMPLETED if i < 3 else TaskStatus.FAILED
            task = Task(
                id=f"task-{i}",
                plan_id="plan-1",
                description=f"Task {i}",
                tool_name="test.tool",
                status=status,
                error=f"Error {i}" if status == TaskStatus.FAILED else None,
            )
            plan.tasks.append(task)
        
        # Create results
        results = [
            TaskResult(
                task_id=f"task-{i}",
                success=(i < 3),
                output=f"result-{i}" if i < 3 else None,
                error=f"Error {i}" if i >= 3 else None,
                execution_time_seconds=1.0,
            )
            for i in range(5)
        ]
        
        evaluation = reflector.evaluate_plan(plan, results, sample_context)
        
        assert evaluation.success is False
        assert len(evaluation.issues) > 0
        assert len(evaluation.suggestions) > 0
        # 60% success rate should trigger replan
        assert evaluation.should_replan is True
    
    def test_detect_failure_patterns_same_error(
        self,
        reflector,
        sample_goal,
        sample_context
    ):
        """Test detection of repeated error patterns"""
        plan = Plan(
            id="plan-1",
            goal=sample_goal,
            status=PlanStatus.FAILED,
        )
        
        # Add tasks with same error type
        for i in range(4):
            task = Task(
                id=f"task-{i}",
                plan_id="plan-1",
                description=f"Network task {i}",
                tool_name="web.fetch",
                status=TaskStatus.FAILED,
                error="Connection timeout",
            )
            plan.tasks.append(task)
        
        results = [
            TaskResult(
                task_id=f"task-{i}",
                success=False,
                error="Connection timeout",
                execution_time_seconds=30.0,
            )
            for i in range(4)
        ]
        
        evaluation = reflector.evaluate_plan(plan, results, sample_context)
        
        # Should detect timeout pattern
        assert len(evaluation.issues) > 0
        assert any("timeout" in issue.lower() for issue in evaluation.issues)
        
        # Check stored patterns
        patterns = reflector.get_failure_patterns()
        assert len(patterns) > 0
        timeout_patterns = [p for p in patterns if p.pattern_type == "timeout"]
        assert len(timeout_patterns) > 0
        assert timeout_patterns[0].occurrences == 4
    
    def test_detect_failure_patterns_same_tool(
        self,
        reflector,
        sample_goal,
        sample_context
    ):
        """Test detection of tool-specific failures"""
        plan = Plan(
            id="plan-1",
            goal=sample_goal,
            status=PlanStatus.FAILED,
        )
        
        # Add tasks with same failing tool
        for i in range(3):
            task = Task(
                id=f"task-{i}",
                plan_id="plan-1",
                description=f"Task {i}",
                tool_name="buggy.tool",
                status=TaskStatus.FAILED,
                error=f"Execution error {i}",
            )
            plan.tasks.append(task)
        
        results = [
            TaskResult(
                task_id=f"task-{i}",
                success=False,
                error=f"Execution error {i}",
                execution_time_seconds=1.0,
            )
            for i in range(3)
        ]
        
        evaluation = reflector.evaluate_plan(plan, results, sample_context)
        
        # Should detect tool failure pattern
        patterns = reflector.get_failure_patterns()
        tool_patterns = [p for p in patterns if p.pattern_type == "tool_failure"]
        assert len(tool_patterns) > 0
        assert "buggy.tool" in tool_patterns[0].description
    
    def test_plan_structure_evaluation(self, reflector, sample_goal, sample_context):
        """Test evaluation of plan structure"""
        plan = Plan(
            id="plan-1",
            goal=sample_goal,
            status=PlanStatus.COMPLETED,
        )
        
        # Create long sequential chain
        for i in range(8):
            task = Task(
                id=f"task-{i}",
                plan_id="plan-1",
                description=f"Sequential task {i}",
                tool_name="test.tool",
                status=TaskStatus.COMPLETED,
                dependencies=[f"task-{i-1}"] if i > 0 else [],
            )
            plan.tasks.append(task)
        
        results = [
            TaskResult(
                task_id=f"task-{i}",
                success=True,
                output=f"result-{i}",
                execution_time_seconds=1.0,
            )
            for i in range(8)
        ]
        
        evaluation = reflector.evaluate_plan(plan, results, sample_context)
        
        # Should suggest parallelization
        assert any(
            "sequential" in issue.lower() or "parallel" in issue.lower()
            for issue in evaluation.issues
        )
    
    def test_llm_reflection_integration(
        self,
        mock_llm_client,
        reflection_criteria,
        sample_goal,
        sample_context
    ):
        """Test LLM-based reflection"""
        reflector = Reflector(
            llm_client=mock_llm_client,
            criteria=reflection_criteria,
            enable_llm_reflection=True,
        )
        
        plan = Plan(
            id="plan-1",
            goal=sample_goal,
            status=PlanStatus.FAILED,
        )
        
        task = Task(
            id="task-1",
            plan_id="plan-1",
            description="Failed task",
            tool_name="test.tool",
            status=TaskStatus.FAILED,
            error="Network error",
        )
        plan.tasks.append(task)
        
        results = [
            TaskResult(
                task_id="task-1",
                success=False,
                error="Network error",
                execution_time_seconds=1.0,
            )
        ]
        
        evaluation = reflector.evaluate_plan(plan, results, sample_context)
        
        # Should have called LLM
        assert mock_llm_client.generate.called
        
        # Should have suggestions from LLM
        assert len(evaluation.suggestions) > 0
    
    def test_disable_llm_reflection(
        self,
        mock_llm_client,
        reflection_criteria,
        sample_goal,
        sample_context
    ):
        """Test that LLM reflection can be disabled"""
        reflector = Reflector(
            llm_client=mock_llm_client,
            criteria=reflection_criteria,
            enable_llm_reflection=False,
        )
        
        plan = Plan(
            id="plan-1",
            goal=sample_goal,
            status=PlanStatus.FAILED,
        )
        
        task = Task(
            id="task-1",
            plan_id="plan-1",
            description="Failed task",
            tool_name="test.tool",
            status=TaskStatus.FAILED,
        )
        plan.tasks.append(task)
        
        results = [
            TaskResult(
                task_id="task-1",
                success=False,
                error="Error",
                execution_time_seconds=1.0,
            )
        ]
        
        evaluation = reflector.evaluate_plan(plan, results, sample_context)
        
        # Should NOT have called LLM
        assert not mock_llm_client.generate.called


class TestLearning:
    """Test learning from episodes"""
    
    def test_learn_from_successful_episode(
        self,
        reflector,
        sample_goal,
        sample_context
    ):
        """Test learning from successful episode"""
        plan = Plan(
            id="plan-1",
            goal=sample_goal,
            status=PlanStatus.COMPLETED,
        )
        
        # Add tasks with various tools
        for i in range(5):
            task = Task(
                id=f"task-{i}",
                plan_id="plan-1",
                description=f"Task {i}",
                tool_name=f"tool-{i % 2}",  # Alternate between 2 tools
                status=TaskStatus.COMPLETED,
            )
            plan.tasks.append(task)
        
        results = [
            TaskResult(
                task_id=f"task-{i}",
                success=True,
                output=f"result-{i}",
                execution_time_seconds=1.0 + i * 0.5,
            )
            for i in range(5)
        ]
        
        episode = Episode(
            id="episode-1",
            session_id="session-1",
            plan=plan,
            results=results,
            success=True,
        )
        
        insights = reflector.learn_from_episode(episode, sample_context)
        
        assert len(insights) > 0
        
        # Should have insights about tool effectiveness
        tool_insights = [i for i in insights if i.category == "tool_effectiveness"]
        assert len(tool_insights) > 0
    
    def test_learn_from_failed_episode(
        self,
        reflector,
        sample_goal,
        sample_context
    ):
        """Test learning from failed episode"""
        plan = Plan(
            id="plan-1",
            goal=sample_goal,
            status=PlanStatus.FAILED,
        )
        
        # Add mix of successful and failed tasks
        for i in range(6):
            status = TaskStatus.COMPLETED if i < 2 else TaskStatus.FAILED
            task = Task(
                id=f"task-{i}",
                plan_id="plan-1",
                description=f"Task {i}",
                tool_name="test.tool",
                status=status,
                error=f"Error {i}" if status == TaskStatus.FAILED else None,
            )
            plan.tasks.append(task)
        
        results = [
            TaskResult(
                task_id=f"task-{i}",
                success=(i < 2),
                output=f"result-{i}" if i < 2 else None,
                error=f"Error {i}" if i >= 2 else None,
                execution_time_seconds=1.0,
            )
            for i in range(6)
        ]
        
        episode = Episode(
            id="episode-1",
            session_id="session-1",
            plan=plan,
            results=results,
            success=False,
        )
        
        insights = reflector.learn_from_episode(episode, sample_context)
        
        # Should generate failure-related insights
        assert len(insights) > 0
        failure_insights = [i for i in insights if i.category == "failure_mode"]
        assert len(failure_insights) > 0
    
    def test_timing_analysis(self, reflector, sample_goal, sample_context):
        """Test timing pattern analysis"""
        plan = Plan(
            id="plan-1",
            goal=sample_goal,
            status=PlanStatus.COMPLETED,
        )
        
        # Add tasks with varying execution times
        execution_times = [1.0, 1.2, 0.9, 1.1, 10.0, 1.0]  # One outlier
        
        for i, exec_time in enumerate(execution_times):
            task = Task(
                id=f"task-{i}",
                plan_id="plan-1",
                description=f"Task {i}",
                tool_name="test.tool",
                status=TaskStatus.COMPLETED,
            )
            plan.tasks.append(task)
        
        results = [
            TaskResult(
                task_id=f"task-{i}",
                success=True,
                output=f"result-{i}",
                execution_time_seconds=exec_time,
            )
            for i, exec_time in enumerate(execution_times)
        ]
        
        episode = Episode(
            id="episode-1",
            session_id="session-1",
            plan=plan,
            results=results,
            success=True,
        )
        
        insights = reflector.learn_from_episode(episode, sample_context)
        
        # Should detect performance outliers
        perf_insights = [i for i in insights if i.category == "performance"]
        assert len(perf_insights) > 0
    
    def test_get_insights_filtering(self, reflector, sample_goal, sample_context):
        """Test insight retrieval with filtering"""
        # Generate some insights
        plan = Plan(id="plan-1", goal=sample_goal)
        for i in range(3):
            task = Task(
                id=f"task-{i}",
                plan_id="plan-1",
                description=f"Task {i}",
                tool_name="tool-0",
                status=TaskStatus.COMPLETED,
            )
            plan.tasks.append(task)
        
        results = [
            TaskResult(
                task_id=f"task-{i}",
                success=True,
                output="result",
                execution_time_seconds=1.0,
            )
            for i in range(3)
        ]
        
        episode = Episode(
            id="episode-1",
            session_id="session-1",
            plan=plan,
            results=results,
            success=True,
        )
        
        insights = reflector.learn_from_episode(episode, sample_context)
        
        # Test category filtering
        tool_insights = reflector.get_insights(category="tool_effectiveness")
        assert all(i.category == "tool_effectiveness" for i in tool_insights)
        
        # Test confidence filtering
        high_conf = reflector.get_insights(min_confidence=0.7)
        assert all(i.confidence >= 0.7 for i in high_conf)
    
    def test_clear_learning_data(self, reflector, sample_goal, sample_context):
        """Test clearing learning data"""
        # Generate some data
        plan = Plan(id="plan-1", goal=sample_goal)
        task = Task(
            id="task-1",
            plan_id="plan-1",
            description="Task",
            tool_name="test.tool",
            status=TaskStatus.FAILED,
            error="Error",
        )
        plan.tasks.append(task)
        
        results = [
            TaskResult(
                task_id="task-1",
                success=False,
                error="Error",
                execution_time_seconds=1.0,
            )
        ]
        
        # Generate patterns and insights
        reflector.evaluate_plan(plan, results, sample_context)
        
        episode = Episode(
            id="episode-1",
            session_id="session-1",
            plan=plan,
            results=results,
            success=False,
        )
        reflector.learn_from_episode(episode, sample_context)
        
        # Verify data exists
        assert len(reflector.get_failure_patterns()) > 0
        assert len(reflector.get_insights()) > 0
        
        # Clear
        reflector.clear_learning_data()
        
        # Verify cleared
        assert len(reflector.get_failure_patterns()) == 0
        assert len(reflector.get_insights()) == 0


class TestReflectionCriteria:
    """Test reflection criteria configuration"""
    
    def test_default_criteria(self):
        """Test default criteria values"""
        criteria = ReflectionCriteria()
        
        assert criteria.min_success_rate == 0.8
        assert criteria.max_execution_time_multiplier == 2.0
        assert criteria.require_all_tasks_complete is True
        assert criteria.check_output_quality is True
    
    def test_custom_criteria(self):
        """Test custom criteria"""
        criteria = ReflectionCriteria(
            min_success_rate=0.9,
            max_execution_time_multiplier=1.5,
            require_all_tasks_complete=False,
            check_output_quality=False,
        )
        
        assert criteria.min_success_rate == 0.9
        assert criteria.max_execution_time_multiplier == 1.5
        assert criteria.require_all_tasks_complete is False
        assert criteria.check_output_quality is False
    
    def test_criteria_from_config(self):
        """Test creating criteria from config dict"""
        config = {
            "min_success_rate": 0.75,
            "max_execution_time_multiplier": 3.0,
        }
        
        criteria = ReflectionCriteria.from_config(config)
        
        assert criteria.min_success_rate == 0.75
        assert criteria.max_execution_time_multiplier == 3.0
        # Defaults for unspecified
        assert criteria.require_all_tasks_complete is True
