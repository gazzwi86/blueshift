"""
Agent Session Logic
===================

Core agent interaction functions for running autonomous coding sessions.

Note: feature_list.json is now stored in project_context/ (not in generations/).
This is managed by lib/core/paths.py.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional, Callable, Any

from claude_code_sdk import ClaudeSDKClient

from .logger import SessionLogger
from ..verification.post_session_validator import run_post_session_verification
from ..core.paths import get_feature_list_path, get_project_context_dir


# Configuration
AUTO_CONTINUE_DELAY_SECONDS = 3

# Categories that REQUIRE deployment verification (not just unit tests)
DEPLOYMENT_REQUIRED_CATEGORIES = {
    "deployment", "infrastructure", "e2e", "evaluation", "integration"
}

# DoD fields that MUST be true for a feature to be truly complete
CRITICAL_DOD_FIELDS = [
    "code_complete",
    "unit_tests_pass",
]

# DoD fields required for deployment/infrastructure features
DEPLOYMENT_DOD_FIELDS = [
    "deployed",
    "smoke_tests_pass",
    "integration_tests_pass",
]

# DoD fields required for evaluation features
EVALUATION_DOD_FIELDS = [
    "evaluation_threshold_met",
]


def check_feature_truly_complete(feature: dict) -> tuple[bool, list[str]]:
    """
    Check if a feature is TRULY complete by verifying its DoD checklist.

    THIS IS THE LAW: A feature is NOT complete unless:
    1. passes == True
    2. All critical DoD fields are True
    3. For deployment/infrastructure/e2e categories: deployed + smoke_tests_pass must be True
    4. For evaluation categories: evaluation_threshold_met must be True

    Args:
        feature: Feature dictionary from feature_list.json

    Returns:
        Tuple of (is_complete, list_of_missing_requirements)
    """
    missing = []

    # Basic check: passes must be true
    if not feature.get("passes"):
        missing.append("passes=false")
        return False, missing

    dod = feature.get("dod_checklist", {})
    category = feature.get("category", "")

    # Check critical DoD fields (required for ALL features)
    for field in CRITICAL_DOD_FIELDS:
        if field in dod and not dod.get(field):
            missing.append(f"dod.{field}=false")

    # Check deployment DoD fields for deployment-related categories
    if category in DEPLOYMENT_REQUIRED_CATEGORIES:
        for field in DEPLOYMENT_DOD_FIELDS:
            if field in dod and not dod.get(field):
                missing.append(f"dod.{field}=false (REQUIRED for {category})")

    # Check evaluation DoD fields for evaluation category
    if category == "evaluation":
        for field in EVALUATION_DOD_FIELDS:
            if field in dod and not dod.get(field):
                missing.append(f"dod.{field}=false (REQUIRED for evaluation)")

    return len(missing) == 0, missing


def check_project_complete(project_dir: Path = None) -> bool:
    """
    Check if project is GENUINELY complete.

    THIS IS THE LAW - A project is NOT complete unless:
    1. ALL features have passes=true
    2. ALL features have their DoD checklists fully satisfied
    3. Deployment/infrastructure features have deployed=true AND smoke_tests_pass=true
    4. Evaluation features have evaluation_threshold_met=true
    5. Integration tests must pass for e2e/integration categories

    This prevents premature completion claims.

    Args:
        project_dir: Deprecated - feature_list.json is now in project_context/

    Returns:
        True if ALL features are genuinely complete, False otherwise
    """
    # feature_list.json is now in project_context/, not project_dir
    feature_list = get_feature_list_path()
    # Reports still go to project_context/
    context_dir = get_project_context_dir()

    if not feature_list.exists():
        return False

    try:
        with open(feature_list) as f:
            data = json.load(f)

        features = data.get("features", [])
        total = data.get("total_features", len(features))

        if total == 0:
            return False

        # Check each feature for TRUE completion
        incomplete_features = []
        for feature in features:
            is_complete, missing = check_feature_truly_complete(feature)
            if not is_complete:
                incomplete_features.append({
                    "id": feature.get("id", "unknown"),
                    "category": feature.get("category", "unknown"),
                    "title": feature.get("title", "unknown"),
                    "missing": missing
                })

        # Log incomplete features for debugging
        if incomplete_features:
            # Write detailed report to project_context directory
            report_path = context_dir / ".completion_check_report.json"
            report = {
                "total_features": total,
                "incomplete_count": len(incomplete_features),
                "complete_count": total - len(incomplete_features),
                "completion_percentage": round((total - len(incomplete_features)) / total * 100, 1),
                "incomplete_features": incomplete_features[:20],  # First 20 for brevity
                "message": "Project is NOT complete. See incomplete_features for details."
            }
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)

            return False

        # All features are truly complete
        return True

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        # Log the error
        error_path = context_dir / ".completion_check_error.txt"
        error_path.write_text(f"Error checking completion: {e}")
        return False


async def run_agent_session(
    client: ClaudeSDKClient,
    message: str,
    project_dir: Path,
    on_tool_use: Optional[Callable[[str, Any], None]] = None,
    session_id: int = 1,
) -> tuple[str, str]:
    """
    Run a single agent session using Claude Agent SDK.

    Args:
        client: Claude SDK client
        message: The prompt to send
        project_dir: Project directory path
        on_tool_use: Optional callback for tool use events
        session_id: Session number for logging

    Returns:
        (status, response_text) where status is:
        - "continue" if agent should continue working
        - "error" if an error occurred
    """
    # Create session logger
    with SessionLogger(project_dir, session_id) as logger:
        logger.log("Sending prompt to Claude Agent SDK...\n")
        logger.log_prompt(message)

        try:
            await client.query(message)

            response_text = ""
            async for msg in client.receive_response():
                msg_type = type(msg).__name__

                # Handle AssistantMessage (text and tool use)
                if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        block_type = type(block).__name__

                        if block_type == "TextBlock" and hasattr(block, "text"):
                            response_text += block.text
                            logger.log_text(block.text)
                        elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                            tool_input = getattr(block, "input", None)
                            logger.log_tool_use(block.name, tool_input)

                            if on_tool_use:
                                on_tool_use(block.name, tool_input)

                # Handle UserMessage (tool results)
                elif msg_type == "UserMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        block_type = type(block).__name__

                        if block_type == "ToolResultBlock":
                            result_content = getattr(block, "content", "")
                            is_error = getattr(block, "is_error", False)
                            is_blocked = "blocked" in str(result_content).lower()

                            logger.log_tool_result(
                                str(result_content),
                                is_error=is_error,
                                is_blocked=is_blocked
                            )

            logger.log("\n" + "-" * 70 + "\n")

            # === HARNESS-CONTROLLED VERIFICATION (THIS IS THE LAW) ===
            # Run post-session verification to validate agent claims
            # The agent CANNOT bypass this - it runs in the harness
            logger.log("\n" + "=" * 70)
            logger.log("  HARNESS VERIFICATION (Agent cannot bypass this)")
            logger.log("=" * 70 + "\n")

            verification_results = run_post_session_verification(project_dir, verbose=True)

            # Log verification results
            infra_passed = verification_results.get("infrastructure", {}).get("passed", False)
            deploy_passed = verification_results.get("deployment", {}).get("passed", False)
            eval_passed = verification_results.get("evaluation", {}).get("passed", False)

            logger.log(f"\nVerification Summary:")
            logger.log(f"  Infrastructure: {'PASS' if infra_passed else 'FAIL'}")
            logger.log(f"  Deployment: {'PASS' if deploy_passed else 'FAIL'}")
            logger.log(f"  Evaluation: {'PASS' if eval_passed else 'FAIL'}")
            logger.log("\n" + "-" * 70 + "\n")

            # Check if project is complete (100% passing)
            # This MUST come AFTER verification which updates feature_list.json
            if check_project_complete(project_dir):
                logger.log("PROJECT COMPLETE: All features passing (100%) - VERIFIED BY HARNESS")
                logger.log_session_end("stop")
                return "stop", response_text
            else:
                logger.log_session_end("continue")
                return "continue", response_text

        except Exception as e:
            logger.log_error(e)
            logger.log_session_end("error")
            return "error", str(e)


class AgentSession:
    """
    Manages a single agent session with context and state.
    """

    def __init__(
        self,
        client: ClaudeSDKClient,
        project_dir: Path,
    ):
        self.client = client
        self.project_dir = project_dir
        self.response_text = ""
        self.tools_used = []

    async def run(self, prompt: str) -> tuple[str, str]:
        """Run the session with the given prompt."""
        def track_tool(name: str, input_data: Any):
            self.tools_used.append({"name": name, "input": input_data})

        return await run_agent_session(
            self.client,
            prompt,
            self.project_dir,
            on_tool_use=track_tool
        )


async def run_autonomous_loop(
    project_dir: Path,
    model: str,
    create_client_fn: Callable,
    get_prompt_fn: Callable[[bool], str],
    is_first_run: bool,
    max_iterations: Optional[int] = None,
    on_session_complete: Optional[Callable[[int, str, str], None]] = None,
) -> None:
    """
    Run the autonomous agent loop.

    Args:
        project_dir: Directory for the project
        model: Claude model to use
        create_client_fn: Function to create a new client
        get_prompt_fn: Function to get the prompt (takes is_first_run)
        is_first_run: Whether this is the first run
        max_iterations: Maximum iterations (None for unlimited)
        on_session_complete: Optional callback after each session
    """
    iteration = 0

    while True:
        iteration += 1

        if max_iterations and iteration > max_iterations:
            print(f"\nReached max iterations ({max_iterations})")
            break

        # Print session header
        session_type = "INITIALIZER" if is_first_run else "CODING AGENT"
        print("\n" + "=" * 70)
        print(f"  SESSION {iteration}: {session_type}")
        print("=" * 70 + "\n")

        # Create fresh client
        client = create_client_fn(project_dir, model)

        # Get prompt
        prompt = get_prompt_fn(is_first_run)
        is_first_run = False  # Only use initializer once

        # Run session
        async with client:
            status, response = await run_agent_session(client, prompt, project_dir)

        if on_session_complete:
            on_session_complete(iteration, status, response)

        if status == "continue":
            print(f"\nAgent will auto-continue in {AUTO_CONTINUE_DELAY_SECONDS}s...")
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)
        elif status == "error":
            print("\nSession encountered an error, will retry...")
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

        if max_iterations is None or iteration < max_iterations:
            print("\nPreparing next session...\n")
            await asyncio.sleep(1)

    print("\n" + "=" * 70)
    print("  SESSION COMPLETE")
    print("=" * 70)
