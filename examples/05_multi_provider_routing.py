"""
Example 05: Multi-Provider LLM Routing
========================================
Demonstrates:
  - LLMRouter fallback strategy: Ollama primary, OpenAI fallback
  - LLMRouter round-robin strategy across two Ollama instances
  - get_usage_stats() per-provider call accounting
  - Router injection into AgentController via agent._llm_client

Requirements:
  - Ollama running on default port: ollama serve
  - Optional: OPENAI_API_KEY in environment for OpenAI fallback demo

Run:
  python examples/05_multi_provider_routing.py
"""

import os

from laios.core.agent import AgentController
from laios.core.types import Config
from laios.llm.clients.ollama import OllamaClient
from laios.llm.router import LLMRouter


PROMPT = "In one sentence, what is the capital of France?"


def demo_fallback_routing(use_openai: bool) -> None:
    """Primary: Ollama. Fallback: OpenAI (if key present) or second Ollama instance."""
    print("--- Fallback Routing ---")

    primary = OllamaClient(model="llama2", base_url="http://localhost:11434")

    if use_openai:
        from laios.llm.clients.openai import OpenAIClient
        fallback = OpenAIClient(model="gpt-3.5-turbo", api_key=os.environ["OPENAI_API_KEY"])
        print("  Providers: Ollama (primary) → OpenAI gpt-3.5-turbo (fallback)")
    else:
        # Use a second Ollama instance on the same host as a stand-in fallback
        fallback = OllamaClient(model="gemma3:4b", base_url="http://localhost:11434")
        print("  Providers: Ollama/llama2 (primary) → Ollama/gemma3:4b (fallback)")

    router = LLMRouter(providers=[primary, fallback], strategy="fallback")

    # Inject router into an AgentController
    config = Config()
    agent = AgentController(config)
    agent._llm_client = router  # replace default client
    session = agent.create_session(user_id="routing_demo")

    try:
        response = agent.process_message(session.id, PROMPT)
        print(f"  Response: {response.strip()}")
    except Exception as exc:
        print(f"  [ERROR] {exc}")
    finally:
        agent.shutdown_session(session.id)

    stats = router.get_usage_stats()
    print("\n  Usage stats:")
    for provider_name, counts in stats.items():
        print(f"    {provider_name}: calls={counts['calls']}, errors={counts['errors']}")


def demo_round_robin_routing() -> None:
    """Round-robin across two Ollama model aliases on the same host."""
    print("\n--- Round-Robin Routing ---")

    client_a = OllamaClient(model="llama2", base_url="http://localhost:11434")
    client_b = OllamaClient(model="llama2", base_url="http://localhost:11434")
    # In a real deployment these would be separate hosts

    router = LLMRouter(providers=[client_a, client_b], strategy="round_robin")
    print("  Providers: OllamaA, OllamaB (round-robin)")

    config = Config()
    agent = AgentController(config)
    agent._llm_client = router
    session = agent.create_session(user_id="rr_demo")

    questions = [
        "What colour is the sky?",
        "What is 2 + 2?",
        "Name one planet in our solar system.",
    ]

    for i, q in enumerate(questions, 1):
        try:
            response = agent.process_message(session.id, q)
            print(f"  Q{i}: {response.strip()[:80]}")
        except Exception as exc:
            print(f"  Q{i}: [ERROR] {exc}")

    agent.shutdown_session(session.id)

    stats = router.get_usage_stats()
    print("\n  Usage stats (should be balanced):")
    for provider_name, counts in stats.items():
        print(f"    {provider_name}: calls={counts['calls']}, errors={counts['errors']}")


def main():
    print("=== Multi-Provider Routing Example ===\n")

    use_openai = bool(os.environ.get("OPENAI_API_KEY"))
    if use_openai:
        print("OPENAI_API_KEY detected — will use OpenAI as fallback.\n")
    else:
        print("No OPENAI_API_KEY — using second Ollama model as fallback.\n")

    demo_fallback_routing(use_openai)
    demo_round_robin_routing()

    print("\nDone.")


if __name__ == "__main__":
    main()
