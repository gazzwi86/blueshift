"""
Human-in-the-Loop (HITL) Checkpoint System

Provides interactive CLI-based checkpoints where the agent pauses execution
and waits for human approval, denial, or feedback before proceeding.

Usage:
    from lib.hitl import HITLCheckpoint, HITLResponse

    checkpoint = HITLCheckpoint(
        name="initializer_complete",
        description="Review generated test fixtures and feature list",
        artifacts=[
            "feature_list.json - 150+ evaluation test cases",
            "fixtures/ - Synthetic test data",
            "init.sh - Environment setup script"
        ],
        review_instructions=[
            "Are the test cases comprehensive?",
            "Is the synthetic data realistic?",
            "Does the project structure make sense?"
        ]
    )

    response = checkpoint.wait_for_approval()

    if response.approved:
        if response.feedback:
            # Handle feedback/amendments before proceeding
            apply_amendments(response.feedback)
        continue_execution()
    else:
        halt_with_reason(response.denial_reason)
"""

import sys
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class HITLDecision(Enum):
    """Possible decisions from human reviewer."""
    APPROVE = "approve"
    DENY = "deny"
    AMEND = "amend"  # Approve with feedback/changes


@dataclass
class HITLResponse:
    """Response from human reviewer at a checkpoint."""
    decision: HITLDecision
    feedback: Optional[str] = None
    denial_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def approved(self) -> bool:
        return self.decision in (HITLDecision.APPROVE, HITLDecision.AMEND)

    @property
    def has_feedback(self) -> bool:
        return bool(self.feedback)

    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "feedback": self.feedback,
            "denial_reason": self.denial_reason,
            "timestamp": self.timestamp.isoformat()
        }


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

    # File to persist checkpoint state (optional)
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

        # Log the decision
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


class HITLManager:
    """
    Manages HITL checkpoints throughout an agent session.

    Provides utilities for:
    - Registering checkpoints
    - Checking if checkpoints are needed
    - Recording checkpoint history
    """

    def __init__(self, history_file: Optional[Path] = None):
        self.history_file = history_file or Path("hitl_history.json")
        self.checkpoints: list[dict] = []
        self._load_history()

    def _load_history(self) -> None:
        """Load checkpoint history from file."""
        if self.history_file.exists():
            try:
                self.checkpoints = json.loads(self.history_file.read_text())
            except json.JSONDecodeError:
                self.checkpoints = []

    def _save_history(self) -> None:
        """Save checkpoint history to file."""
        self.history_file.write_text(json.dumps(self.checkpoints, indent=2))

    def checkpoint(
        self,
        name: str,
        description: str,
        artifacts: list[str] = None,
        review_instructions: list[str] = None,
        context: dict = None
    ) -> HITLResponse:
        """
        Create and execute a checkpoint.

        Args:
            name: Unique identifier for this checkpoint
            description: Human-readable description
            artifacts: List of artifacts to review
            review_instructions: Questions/instructions for reviewer
            context: Additional context data

        Returns:
            HITLResponse with the human's decision
        """
        checkpoint = HITLCheckpoint(
            name=name,
            description=description,
            artifacts=artifacts or [],
            review_instructions=review_instructions or [],
            context=context or {}
        )

        response = checkpoint.wait_for_approval()

        # Record in history
        self.checkpoints.append({
            "name": name,
            "description": description,
            "response": response.to_dict()
        })
        self._save_history()

        return response

    def require_approval(
        self,
        name: str,
        description: str,
        **kwargs
    ) -> None:
        """
        Execute a checkpoint and raise if not approved.

        This is a convenience method for checkpoints where denial
        should halt execution entirely.

        Raises:
            SystemExit: If checkpoint is denied
        """
        response = self.checkpoint(name, description, **kwargs)

        if not response.approved:
            print(f"\n  CHECKPOINT DENIED: {name}")
            print(f"  Reason: {response.denial_reason}")
            print("\n  Agent execution halted.")
            sys.exit(1)

        return response


# Convenience functions for simple usage
_manager: Optional[HITLManager] = None

def get_manager() -> HITLManager:
    """Get or create the global HITL manager."""
    global _manager
    if _manager is None:
        _manager = HITLManager()
    return _manager


def checkpoint(
    name: str,
    description: str,
    artifacts: list[str] = None,
    review_instructions: list[str] = None,
    context: dict = None
) -> HITLResponse:
    """Create and execute a HITL checkpoint."""
    return get_manager().checkpoint(
        name, description, artifacts, review_instructions, context
    )


def require_approval(name: str, description: str, **kwargs) -> HITLResponse:
    """Execute a checkpoint that halts on denial."""
    return get_manager().require_approval(name, description, **kwargs)


# Example usage for testing
if __name__ == "__main__":
    # Demo the HITL system
    response = checkpoint(
        name="demo_checkpoint",
        description="This is a demonstration of the HITL system",
        artifacts=[
            "feature_list.json - Test cases",
            "fixtures/ - Test data"
        ],
        review_instructions=[
            "Is everything looking good?",
            "Any changes needed?"
        ],
        context={
            "tests_generated": 150,
            "categories": 7
        }
    )

    print(f"\nResult: {response.decision.value}")
    print(f"Approved: {response.approved}")
    if response.feedback:
        print(f"Feedback: {response.feedback}")
