"""
Tests for LLM integration

Note: These tests require Ollama to be running and a model to be available.
"""

import pytest

from laios.llm.client import LLMMessage
from laios.llm.prompts import CHAT_SYSTEM_PROMPT, fill_template


class TestLLMMessage:
    """Tests for LLMMessage"""
    
    def test_message_creation(self):
        """Test creating an LLM message"""
        msg = LLMMessage(role="user", content="Hello")
        
        assert msg.role == "user"
        assert msg.content == "Hello"


class TestPrompts:
    """Tests for prompt templates"""
    
    def test_system_prompt_exists(self):
        """Test that system prompt is defined"""
        assert CHAT_SYSTEM_PROMPT
        assert len(CHAT_SYSTEM_PROMPT) > 100
        assert "LAIOS" in CHAT_SYSTEM_PROMPT
    
    def test_fill_template(self):
        """Test template filling"""
        template = "Hello, {name}! You are {age} years old."
        result = fill_template(template, name="Alice", age=30)
        
        assert result == "Hello, Alice! You are 30 years old."


# Tests requiring Ollama running
@pytest.mark.skipif(True, reason="Requires Ollama running - run manually")
class TestOllamaClient:
    """Tests for Ollama client (manual)"""
    
    def test_ollama_initialization(self):
        """Test initializing Ollama client"""
        from laios.llm.providers.ollama import OllamaClient
        
        client = OllamaClient(model="llama2")
        assert client.model == "llama2"
    
    def test_ollama_generation(self):
        """Test generating response"""
        from laios.llm.providers.ollama import OllamaClient
        
        client = OllamaClient(model="llama2")
        
        response = client.generate_with_system(
            system_prompt="You are a helpful assistant.",
            user_message="Say 'Hello, LAIOS!' and nothing else.",
            temperature=0.0,
            max_tokens=50
        )
        
        assert response.success
        assert "LAIOS" in response.content or "Hello" in response.content
        assert response.model == "llama2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
