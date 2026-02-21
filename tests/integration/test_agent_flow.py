"""
Basic integration test for agent flow
"""

import pytest

from laios.core.agent import AgentController
from laios.core.config import Config
from laios.core.types import Goal


class TestAgentFlow:
    """Test full agent pipeline"""
    
    @pytest.fixture
    def agent(self):
        """Create agent with default config"""
        config = Config()
        return AgentController(config)
    
    def test_session_creation(self, agent):
        """Test creating and managing sessions"""
        session = agent.create_session(user_id="test_user")
        
        assert session is not None
        assert session.user_id == "test_user"
        assert session.active is True
        
        # Retrieve session
        retrieved = agent.get_session(session.id)
        assert retrieved is not None
        assert retrieved.id == session.id
        
        # Shutdown session
        agent.shutdown_session(session.id)
        assert session.id not in agent.sessions
    
    def test_process_message(self, agent):
        """Test processing user message"""
        session = agent.create_session(user_id="test_user")
        
        response = agent.process_message(
            session.id,
            "Hello, LAIOS!"
        )
        
        assert response is not None
        assert isinstance(response, str)
        assert len(session.context.messages) == 2  # user + assistant
    
    def test_execute_goal(self, agent):
        """Test executing structured goal"""
        session = agent.create_session(user_id="test_user")
        goal = Goal(description="Test goal execution")
        
        result = agent.execute_goal(session.id, goal)
        
        assert result is not None
        assert "goal" in result
        assert result["goal"] == goal


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
