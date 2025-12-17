#!/usr/bin/env python3
"""
Ultra Coding Agent - Entry Point
================================

Start the autonomous coding agent with project-specific configuration.

Example Usage:
    python start.py --project-dir ./my_project
    python start.py --project-dir ./my_project --max-iterations 5
"""

import argparse
import asyncio
import os
import subprocess
from pathlib import Path

# Import library modules
from lib.orchestrator.session import run_agent_session
from lib.progress import print_session_header, print_progress_summary, ProgressTracker
from lib.prompts import get_initializer_prompt, get_coding_prompt, copy_spec_to_project
from lib.hitl import checkpoint, HITLDecision

# Import project-specific modules
from credentials import get_credentials, print_credential_status, validate_credentials
from client import create_client


# Configuration
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
AUTO_CONTINUE_DELAY_SECONDS = 3


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Ultra Coding Agent - Autonomous AI development harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start fresh project
  python start.py --project-dir ./pixieops

  # Use a specific model
  python start.py --project-dir ./pixieops --model claude-sonnet-4-5-20250929

  # Limit iterations for testing
  python start.py --project-dir ./pixieops --max-iterations 5

Environment Variables:
  ANTHROPIC_API_KEY    Your Anthropic API key (optional if using Claude Code subscription)
        """,
    )

    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("./generations/autonomous_demo_project"),
        help="Directory for the project (default: generations/autonomous_demo_project)",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum number of agent iterations (default: unlimited)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Claude model to use (default: {DEFAULT_MODEL})",
    )

    return parser.parse_args()


async def run_autonomous_agent(
    project_dir: Path,
    model: str,
    max_iterations: int | None = None,
) -> None:
    """
    Run the autonomous agent loop.

    Args:
        project_dir: Directory for the project
        model: Claude model to use
        max_iterations: Maximum number of iterations (None for unlimited)
    """
    print("\n" + "=" * 70)
    print("  ULTRA CODING AGENT")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print(f"Model: {model}")
    if max_iterations:
        print(f"Max iterations: {max_iterations}")
    else:
        print("Max iterations: Unlimited (will run until completion)")
    print()

    # Load and validate credentials
    print("Loading credentials...")
    creds = get_credentials()
    print_credential_status(creds)

    # Show warnings for missing optional credentials
    warnings = validate_credentials(creds, require_all=False)
    for warning in warnings:
        print(f"  {warning}")
    print()

    # Create project directory
    project_dir.mkdir(parents=True, exist_ok=True)

    # Initialize git repository in the project directory if it doesn't exist
    # This keeps the generated project separate from the harness repository
    project_git_dir = project_dir / ".git"
    if not project_git_dir.exists():
        print("Initializing git repository in project directory...")
        result = subprocess.run(
            ["git", "init"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  Created git repository in {project_dir}")
            # Create initial .gitignore
            gitignore = project_dir / ".gitignore"
            if not gitignore.exists():
                gitignore.write_text(
                    "# Python\n"
                    "__pycache__/\n"
                    "*.pyc\n"
                    ".venv/\n"
                    "venv/\n"
                    "\n"
                    "# Environment\n"
                    ".env\n"
                    ".env.local\n"
                    "\n"
                    "# IDE\n"
                    ".idea/\n"
                    ".vscode/\n"
                    "\n"
                    "# Logs\n"
                    "logs/\n"
                    "*.log\n"
                    "\n"
                    "# Terraform\n"
                    ".terraform/\n"
                    "*.tfstate*\n"
                )
                print("  Created .gitignore")
        else:
            print(f"  Warning: git init failed: {result.stderr}")
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
        # Copy the app spec into the project directory
        copy_spec_to_project(project_dir)

        # Copy .env to project directory if it exists and hasn't been copied
        harness_env = Path(__file__).parent / ".env"
        project_env = project_dir / ".env"
        if harness_env.exists() and not project_env.exists():
            import shutil
            shutil.copy(harness_env, project_env)
            print(f"Copied .env to {project_dir}")
            print("  (The agent can modify this for project-specific needs)")
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
        client = create_client(project_dir, model, creds)

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

            # Read checkpoint details
            checkpoint_content = hitl_file.read_text()

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
        if status == "continue":
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


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Load .env file first
    from credentials import load_env_file
    load_env_file()

    # Check for API key (optional - Claude Code subscription token works too)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Note: ANTHROPIC_API_KEY not set. Using Claude Code subscription token.")
        print("      (If you want to use API credits, set ANTHROPIC_API_KEY in .env)")
        print()

    # Normalize project directory
    project_dir = args.project_dir
    if not project_dir.is_absolute() and not str(project_dir).startswith("generations/"):
        project_dir = Path("generations") / project_dir

    # Run the agent
    try:
        asyncio.run(
            run_autonomous_agent(
                project_dir=project_dir,
                model=args.model,
                max_iterations=args.max_iterations,
            )
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        print("To resume, run the same command again")
    except Exception as e:
        print(f"\nFatal error: {e}")
        raise


if __name__ == "__main__":
    main()
