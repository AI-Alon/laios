"""
Example 04: Streaming Chat Output
===================================
Demonstrates:
  - process_message_stream() with live token-by-token output
  - Side-by-side timing comparison: streaming vs. non-streaming
  - Graceful Ollama connection error handling

Requirements:
  - Ollama running: ollama serve
  - Model pulled:   ollama pull llama2

Run:
  python examples/04_streaming.py
"""

import sys
import time

from laios.core.agent import AgentController
from laios.core.types import Config


PROMPT = "Write a short paragraph explaining why local AI agents are useful."


def run_non_streaming(agent, session_id: str) -> tuple[str, float]:
    """Returns (response_text, elapsed_seconds)."""
    start = time.perf_counter()
    response = agent.process_message(session_id, PROMPT)
    elapsed = time.perf_counter() - start
    return response, elapsed


def run_streaming(agent, session_id: str) -> tuple[str, float]:
    """Prints tokens as they arrive; returns (full_text, elapsed_seconds)."""
    chunks = []
    start = time.perf_counter()
    for chunk in agent.process_message_stream(session_id, PROMPT):
        sys.stdout.write(chunk)
        sys.stdout.flush()
        chunks.append(chunk)
    elapsed = time.perf_counter() - start
    print()  # newline after stream ends
    return "".join(chunks), elapsed


def main():
    print("=== Streaming Chat Example ===\n")

    config = Config()

    # ── Non-streaming run ──────────────────────────────────────────────────────
    print("--- Non-Streaming ---")
    print(f"Prompt: {PROMPT}\n")

    agent = AgentController(config)
    session = agent.create_session(user_id="stream_demo")

    try:
        response, non_stream_time = run_non_streaming(agent, session.id)
    except Exception as exc:
        print(f"[ERROR] Could not reach Ollama: {exc}")
        print("Make sure `ollama serve` is running and the model is pulled.")
        agent.shutdown_session(session.id)
        return

    print(f"Response ({len(response)} chars):")
    print(response)
    print(f"\nTime (non-streaming): {non_stream_time:.2f}s")

    agent.shutdown_session(session.id)

    # ── Streaming run ──────────────────────────────────────────────────────────
    print("\n--- Streaming (tokens appear as they arrive) ---")
    print(f"Prompt: {PROMPT}\n")

    agent2 = AgentController(config)
    session2 = agent2.create_session(user_id="stream_demo_2")

    try:
        full_text, stream_time = run_streaming(agent2, session2.id)
    except Exception as exc:
        print(f"\n[ERROR] Streaming failed: {exc}")
        agent2.shutdown_session(session2.id)
        return

    agent2.shutdown_session(session2.id)

    # ── Comparison ──────────────────────────────────────────────────────────────
    print("\n--- Timing Comparison ---")
    print(f"  Non-streaming : {non_stream_time:.2f}s  (blocks until complete)")
    print(f"  Streaming     : {stream_time:.2f}s  (first token appears faster)")
    print(f"\n  Response length match: {len(response)} vs {len(full_text)} chars")

    print("\nDone.")


if __name__ == "__main__":
    main()
