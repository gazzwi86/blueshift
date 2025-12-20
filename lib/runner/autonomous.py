"""
Autonomous Agent Loop
=====================

Core logic for running the autonomous agent loop.
"""

import asyncio
from pathlib import Path
from typing import Optional

from ..progress import ProgressTracker, print_session_header, print_progress_summary
from ..prompts import get_initializer_prompt, get_coding_prompt
from ..hitl import checkpoint, HITLDecision
from ..orchestrator.session import run_agent_session


# Configuration
AUTO_CONTINUE_DELAY_SECONDS = 3


async def run_autonomous_agent(
    project_dir: Path,
    model: str,
    create_client_fn,
    creds,
    max_iterations: Optional[int] = None,
) -> None:
    """
    Run the autonomous agent loop.

    Args:
        project_dir: Directory for the project
        model: Claude model to use
        create_client_fn: Function to create the Claude client
        creds: Credentials for the client
        max_iterations: Maximum number of iterations (None for unlimited)
    """
    print("\n" + "=" * 70)
    print("  BLUESHIFT AUTONOMOUS AGENT")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print(f"Model: {model}")
    if max_iterations:
        print(f"Max iterations: {max_iterations}")
    else:
        print("Max iterations: Unlimited (will run until completion)")
    print()

    # Initialize progress tracker
    tracker = ProgressTracker(project_dir)
    is_first_run = tracker.is_first_run()

    if is_first_run:
        print("Fresh start - will use initializer agent")
        print()
        print("=" * 70)
        print("  NOTE: First session may take 10-20+ minutes!")
        print("  The agent is generating evaluation test cases and fixtures.")
        print("  Watch for [Tool: ...] output to confirm the agent is working.")
        print("=" * 70)
        print()
    else:
        print("Continuing existing project")
        print_progress_summary(project_dir)

    # Main loop
    iteration = 0

    while True:
        iteration += 1

        # Check max iterations
        if max_iterations and iteration > max_iterations:
            print(f"\nReached max iterations ({max_iterations})")
            print("To continue, run the script again without --max-iterations")
            break

        # Print session header
        print_session_header(iteration, is_first_run)

        # Create client (fresh context) with credentials
        client = create_client_fn(project_dir, model, creds)

        # Choose prompt based on session type
        used_initializer = False
        if is_first_run:
            prompt = get_initializer_prompt()
            used_initializer = True
            is_first_run = False  # Only use initializer once
        else:
            prompt = get_coding_prompt()

        # Run session with async context manager
        async with client:
            status, response = await run_agent_session(client, prompt, project_dir, session_id=iteration)

        # Check for HITL checkpoint file
        hitl_file = project_dir / "HITL_CHECKPOINT.md"
        hitl_feedback_file = project_dir / "HITL_FEEDBACK.md"

        # If initializer session completed but didn't create HITL checkpoint, warn
        if used_initializer and not hitl_file.exists():
            print("\n" + "=" * 70)
            print("  WARNING: Initializer completed without HITL checkpoint")
            print("=" * 70)
            print("\nThe initializer should create HITL_CHECKPOINT.md for review.")
            print("This may indicate the agent didn't complete initialization properly.")
            print("\nOptions:")
            print("  1. Review generated files manually")
            print("  2. Create HITL_CHECKPOINT.md yourself if needed")
            print("  3. Continue anyway (may skip human review)")
            print()

            # Force a HITL checkpoint for initializer
            result = checkpoint(
                name="initializer_review",
                description="Initializer completed - please review generated files before continuing.",
                artifacts=[
                    str(project_dir / "feature_list.json"),
                    str(project_dir / "fixtures"),
                ],
                review_instructions=[
                    "Review feature_list.json for completeness",
                    "Check that tech_stack tests match app_spec.txt requirements",
                    "Verify fixtures are realistic",
                    "Approve to continue to coding phase"
                ]
            )

            if result.decision == HITLDecision.DENY:
                print("\nAgent halted by human decision.")
                print(f"Reason: {result.denial_reason}")
                break

            if result.feedback:
                # Write feedback to a file the agent can read
                hitl_feedback_file.write_text(f"# HITL Feedback\n\n{result.feedback}\n")
                tracker.update_progress(
                    iteration,
                    "CONTINUING",
                    f"HITL feedback: {result.feedback}"
                )

        if hitl_file.exists():
            print("\n" + "=" * 70)
            print("  HITL CHECKPOINT DETECTED")
            print("=" * 70)

            # Display and get human decision
            result = checkpoint(
                name="agent_checkpoint",
                description="The agent has reached a checkpoint requiring human review.",
                artifacts=[str(hitl_file)],
                review_instructions=[
                    "Review the checkpoint file for details",
                    "Make any necessary adjustments",
                    "Approve to continue or deny to halt"
                ]
            )

            if result.decision == HITLDecision.DENY:
                print("\nAgent halted by human decision.")
                print(f"Reason: {result.denial_reason}")
                break

            # Remove checkpoint file to continue
            hitl_file.unlink()

            if result.feedback:
                # Write feedback to progress file
                tracker.update_progress(
                    iteration,
                    "CONTINUING",
                    f"HITL feedback: {result.feedback}"
                )

        # Handle status
        if status == "stop":
            print("\n" + "=" * 70)
            print("  PROJECT COMPLETE!")
            print("=" * 70)
            print("\nAll features passing (100%). Agent has finished work.")
            print_progress_summary(project_dir)
            break

        elif status == "continue":
            print(f"\nAgent will auto-continue in {AUTO_CONTINUE_DELAY_SECONDS}s...")
            print_progress_summary(project_dir)
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

        elif status == "error":
            print("\nSession encountered an error")
            print("Will retry with a fresh session...")
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

        # Small delay between sessions
        if max_iterations is None or iteration < max_iterations:
            print("\nPreparing next session...\n")
            await asyncio.sleep(1)

    # Final summary
    _print_final_summary(project_dir)


def _print_final_summary(project_dir: Path) -> None:
    """Print the final summary after agent completion."""
    print("\n" + "=" * 70)
    print("  SESSION COMPLETE")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print_progress_summary(project_dir)

    print("\n" + "-" * 70)
    print("  TO RUN THE GENERATED APPLICATION:")
    print("-" * 70)
    print(f"\n  cd {project_dir.resolve()}")
    print("  ./init.sh           # Run the setup script")
    print("-" * 70)

    print("\nDone!")
