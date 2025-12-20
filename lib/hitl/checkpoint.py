"""
HITL Checkpoint Implementation
==============================

Interactive checkpoint that pauses for human review.
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .types import HITLDecision, HITLResponse


@dataclass
class HITLCheckpoint:
    """
    A checkpoint that pauses agent execution for human review.

    The agent displays information about what was accomplished and what
    needs review, then waits for the human to approve, deny, or provide
    amendments before continuing.
    """
    name: str
    description: str
    artifacts: list[str] = field(default_factory=list)
    review_instructions: list[str] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    checkpoint_file: Optional[Path] = None

    def display(self) -> None:
        """Display the checkpoint information to the user."""
        border = "=" * 70

        print(f"\n{border}")
        print("  HUMAN-IN-THE-LOOP CHECKPOINT")
        print(border)
        print(f"\n  Checkpoint: {self.name}")
        print(f"  {self.description}")

        if self.artifacts:
            print("\n  Generated Artifacts:")
            for artifact in self.artifacts:
                print(f"    - {artifact}")

        if self.review_instructions:
            print("\n  Please Review:")
            for i, instruction in enumerate(self.review_instructions, 1):
                print(f"    {i}. {instruction}")

        if self.context:
            print("\n  Context:")
            for key, value in self.context.items():
                print(f"    {key}: {value}")

        print(f"\n{border}\n")

    def prompt_decision(self) -> HITLResponse:
        """
        Prompt the user for their decision via CLI.

        Returns:
            HITLResponse with the user's decision and any feedback.
        """
        self.display()

        print("  Options:")
        print("    [A] Approve - Continue with execution")
        print("    [D] Deny    - Halt execution (provide reason)")
        print("    [M] Amend   - Approve with feedback/changes")
        print()

        while True:
            try:
                choice = input("  Your decision (A/D/M): ").strip().upper()

                if choice == 'A':
                    return HITLResponse(decision=HITLDecision.APPROVE)

                elif choice == 'D':
                    print()
                    reason = input("  Reason for denial: ").strip()
                    return HITLResponse(
                        decision=HITLDecision.DENY,
                        denial_reason=reason or "No reason provided"
                    )

                elif choice == 'M':
                    print()
                    print("  Enter your feedback/amendments (press Enter twice to finish):")
                    lines = []
                    while True:
                        line = input("  > ")
                        if line == "":
                            if lines:
                                break
                        else:
                            lines.append(line)

                    feedback = "\n".join(lines)
                    return HITLResponse(
                        decision=HITLDecision.AMEND,
                        feedback=feedback
                    )

                else:
                    print("  Invalid choice. Please enter A, D, or M.")

            except KeyboardInterrupt:
                print("\n\n  Checkpoint interrupted. Treating as DENY.")
                return HITLResponse(
                    decision=HITLDecision.DENY,
                    denial_reason="Interrupted by user (Ctrl+C)"
                )
            except EOFError:
                print("\n  No input available. Treating as DENY.")
                return HITLResponse(
                    decision=HITLDecision.DENY,
                    denial_reason="No input available (non-interactive mode)"
                )

    def wait_for_approval(self, save_response: bool = True) -> HITLResponse:
        """
        Display checkpoint and wait for human decision.

        Args:
            save_response: If True, save the response to a file for audit trail.

        Returns:
            HITLResponse with the human's decision.
        """
        response = self.prompt_decision()

        if save_response and self.checkpoint_file:
            self._save_response(response)

        self._log_decision(response)

        return response

    def _save_response(self, response: HITLResponse) -> None:
        """Save the response to checkpoint file."""
        if not self.checkpoint_file:
            return

        checkpoint_data = {
            "checkpoint_name": self.name,
            "description": self.description,
            "response": response.to_dict()
        }

        self.checkpoint_file.write_text(json.dumps(checkpoint_data, indent=2))

    def _log_decision(self, response: HITLResponse) -> None:
        """Log the decision for visibility."""
        decision_str = response.decision.value.upper()

        print()
        print(f"  Decision: {decision_str}")

        if response.feedback:
            print(f"  Feedback: {response.feedback[:100]}...")

        if response.denial_reason:
            print(f"  Reason: {response.denial_reason}")

        print()


# Convenience functions
def checkpoint(
    name: str,
    description: str,
    artifacts: list[str] = None,
    review_instructions: list[str] = None,
    context: dict = None
) -> HITLResponse:
    """
    Create and execute a HITL checkpoint.

    This is the main entry point for creating checkpoints.

    Args:
        name: Unique identifier for this checkpoint
        description: Human-readable description
        artifacts: List of artifacts to review
        review_instructions: Questions/instructions for reviewer
        context: Additional context data

    Returns:
        HITLResponse with the human's decision
    """
    from .manager import get_manager
    return get_manager().checkpoint(
        name, description, artifacts, review_instructions, context
    )


def require_approval(name: str, description: str, **kwargs) -> HITLResponse:
    """
    Execute a checkpoint that exits on denial.

    Args:
        name: Unique identifier for this checkpoint
        description: Human-readable description
        **kwargs: Additional checkpoint arguments

    Returns:
        HITLResponse (only if approved)

    Raises:
        SystemExit: If checkpoint is denied
    """
    from .manager import get_manager
    return get_manager().require_approval(name, description, **kwargs)
