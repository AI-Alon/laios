"""
Example 02: Autonomous Code Reviewer
======================================
Demonstrates:
  - execute_goal() with AUTONOMOUS trust level
  - Inspecting TaskResult objects (success, output, timing)
  - Replanning tracking (replanning_attempts)
  - Episode retrieval from MemoryStore

Requirements:
  - Ollama running: ollama serve
  - Model pulled:   ollama pull llama2

Run:
  python examples/02_code_reviewer.py               # reviews README.md
  python examples/02_code_reviewer.py path/to/file  # reviews a specific file
"""

import sys
from laios.core.agent import AgentController
from laios.core.types import Config, AgentConfig, TrustLevel, Goal


def main():
    target_file = sys.argv[1] if len(sys.argv) > 1 else "README.md"

    print(f"=== Code Reviewer Example ===")
    print(f"Target file: {target_file}\n")

    # Use AUTONOMOUS trust level — no approval prompts
    config = Config(
        agent=AgentConfig(
            trust_level=TrustLevel.AUTONOMOUS,
            enable_reflection=True,
            max_replanning_attempts=1,
        )
    )
    agent = AgentController(config)
    session = agent.create_session(user_id="reviewer")

    goal = Goal(
        description=(
            f"Read the file '{target_file}', analyze its structure and content quality, "
            f"then provide a structured report covering: purpose, strengths, weaknesses, "
            f"and 3 specific improvement suggestions."
        ),
        constraints={"max_time_seconds": 120},
        priority=8,
    )

    print("Executing review goal...")
    result = agent.execute_goal(session.id, goal)

    # Summary
    print(f"\n--- Results ---")
    print(f"Overall success:      {result['success']}")
    print(f"Tasks planned:        {len(result['plan']['tasks'])}")
    print(f"Tasks executed:       {len(result['results'])}")
    print(f"Replanning attempts:  {result['replanning_attempts']}")
    print(f"Episode ID:           {result['episode_id'][:8]}...")

    # Per-task breakdown
    print(f"\n--- Task Breakdown ---")
    for task_result in result["results"]:
        status = "OK  " if task_result["success"] else "FAIL"
        time_ms = task_result["execution_time_seconds"] * 1000
        print(f"  [{status}] {task_result['task_id'][:8]} — {time_ms:.0f}ms")
        if not task_result["success"]:
            print(f"         Error: {task_result['error']}")
        elif task_result.get("output"):
            preview = str(task_result["output"])[:150]
            print(f"         {preview}...")

    # Retrieve the stored episode
    memory = agent.get_memory()
    episode = memory.get_episode(result["episode_id"])
    if episode:
        print(f"\n--- Episode Record ---")
        print(f"Episode ID:  {episode.id[:8]}...")
        print(f"Session:     {episode.session_id[:8]}...")
        print(f"Tasks:       {len(episode.plan.tasks)}")
        print(f"Success:     {episode.success}")
        print(f"Created:     {episode.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

    agent.shutdown_session(session.id)
    print("\nDone.")


if __name__ == "__main__":
    main()
