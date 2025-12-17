"""
Agent Session Logic
===================

Core agent interaction functions for running autonomous coding sessions.
"""

import asyncio
from pathlib import Path
from typing import Optional, Callable, Any

from claude_code_sdk import ClaudeSDKClient

from .logger import SessionLogger


# Configuration
AUTO_CONTINUE_DELAY_SECONDS = 3


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
