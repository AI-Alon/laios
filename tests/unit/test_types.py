"""
Basic tests for core types and models
"""

import pytest
from datetime import datetime

from laios.core.types import (
    Goal,
    Task,
    Plan,
    TaskStatus,
    PlanStatus,
    Intent,
    Tool,
    Permission,
)


class TestGoal:
    """Tests for Goal model"""
    
    def test_goal_creation(self):
        goal = Goal(description="Test goal")
        
        assert goal.description == "Test goal"
        assert goal.priority == 5  # default
        assert isinstance(goal.created_at, datetime)
    
    def test_goal_with_constraints(self):
        goal = Goal(
            description="Test goal",
            constraints={"max_time": 60},
            priority=8
        )
        
        assert goal.constraints["max_time"] == 60
        assert goal.priority == 8


class TestTask:
    """Tests for Task model"""
    
    def test_task_creation(self):
        task = Task(
            plan_id="plan_123",
            description="Test task",
            tool_name="test_tool"
        )
        
        assert task.description == "Test task"
        assert task.status == TaskStatus.PENDING
        assert task.dependencies == []
    
    def test_task_with_dependencies(self):
        task = Task(
            plan_id="plan_123",
            description="Dependent task",
            tool_name="test_tool",
            dependencies=["task_1", "task_2"]
        )
        
        assert len(task.dependencies) == 2
        assert "task_1" in task.dependencies


class TestPlan:
    """Tests for Plan model"""
    
    def test_plan_creation(self):
        goal = Goal(description="Test goal")
        plan = Plan(goal=goal)
        
        assert plan.goal == goal
        assert plan.status == PlanStatus.DRAFT
        assert len(plan.tasks) == 0
    
    def test_get_task(self):
        goal = Goal(description="Test goal")
        plan = Plan(goal=goal)
        
        task = Task(
            plan_id=plan.id,
            description="Task 1",
            tool_name="tool_1"
        )
        plan.tasks.append(task)
        
        retrieved = plan.get_task(task.id)
        assert retrieved is not None
        assert retrieved.id == task.id
    
    def test_get_ready_tasks(self):
        goal = Goal(description="Test goal")
        plan = Plan(goal=goal)
        
        task1 = Task(
            plan_id=plan.id,
            description="Task 1",
            tool_name="tool_1",
            status=TaskStatus.PENDING
        )
        
        task2 = Task(
            plan_id=plan.id,
            description="Task 2",
            tool_name="tool_2",
            dependencies=[task1.id],
            status=TaskStatus.PENDING
        )
        
        plan.tasks = [task1, task2]
        
        # Task 1 should be ready (no dependencies)
        ready = plan.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == task1.id
        
        # After task1 completes, task2 should be ready
        task1.status = TaskStatus.COMPLETED
        ready = plan.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == task2.id


class TestTool:
    """Tests for Tool model"""
    
    def test_tool_creation(self):
        tool = Tool(
            name="test_tool",
            description="A test tool",
            permissions={Permission.FILESYSTEM_READ}
        )
        
        assert tool.name == "test_tool"
        assert Permission.FILESYSTEM_READ in tool.permissions
        assert tool.enabled is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
