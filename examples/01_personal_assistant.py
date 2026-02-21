"""
Example 01: Personal Assistant
================================
Demonstrates:
  - AgentController initialization with default config
  - Pre-seeding long-term memory so the agent "knows" the user
  - Multi-turn conversation with process_message()
  - Session state inspection
  - Session shutdown

Requirements:
  - Ollama running: ollama serve
  - Model pulled:   ollama pull llama2

Run: python examples/01_personal_assistant.py
"""

from laios.core.agent import AgentController
from laios.core.types import Config


def main():
    print("=== Personal Assistant Example ===\n")

    # Initialize with default config (ollama / llama2 / balanced trust)
    config = Config()
    agent = AgentController(config)
    memory = agent.get_memory()

    # Pre-seed long-term memory — the agent will find these on the first message
    print("Seeding long-term memory...")
    memory.store_long_term(
        "The user is a Python developer who prefers concise, type-annotated code",
        metadata={"source": "onboarding", "topic": "user_preferences"},
    )
    memory.store_long_term(
        "The user's main project is an AI-powered code review tool built with LAIOS",
        metadata={"source": "onboarding", "topic": "project_context"},
    )
    print("  Stored 2 long-term memories.\n")

    # Create session
    session = agent.create_session(user_id="demo_user")
    print(f"Session: {session.id[:8]}...\n")

    # Multi-turn conversation
    turns = [
        "What do you know about me and my project?",
        "What's your advice for keeping Python code maintainable?",
        "Thanks, that's helpful!",
    ]

    for user_msg in turns:
        print(f"User:  {user_msg}")
        response = agent.process_message(session.id, user_msg)
        print(f"Agent: {response[:200]}{'...' if len(response) > 200 else ''}\n")

    # Show session state
    state = agent.get_session_state(session.id)
    print("--- Session State ---")
    print(f"  Messages in session:  {state['message_count']}")
    print(f"  LLM available:        {state['llm_available']}")
    print(f"  Reflection enabled:   {state['reflection_enabled']}")
    print(f"  Tools registered:     {state['tools_registered']}")

    # Clean up
    agent.shutdown_session(session.id)
    print("\nSession closed.")


if __name__ == "__main__":
    main()
