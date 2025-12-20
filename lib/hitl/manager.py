"""
HITL Manager
============

Manages HITL checkpoints and maintains history.
"""

import json
import sys
from pathlib import Path
from typing import Optional

from .types import HITLDecision, HITLResponse, HITLCheckpointRecord
from .checkpoint import HITLCheckpoint


class HITLManager:
    """
    Manages HITL checkpoints throughout an agent session.

    Provides utilities for:
    - Registering checkpoints
    - Checking if checkpoints are needed
    - Recording checkpoint history
    """

    def __init__(self, history_file: Optional[Path] = None):
        """
        Initialize the HITL manager.

        Args:
            history_file: Path to store checkpoint history.
                         Defaults to project_context/hitl_history.json
        """
        if history_file is None:
            from ..core.paths import get_hitl_history_path
            history_file = get_hitl_history_path()

        self.history_file = history_file
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
        # Ensure parent directory exists
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
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
        cp = HITLCheckpoint(
            name=name,
            description=description,
            artifacts=artifacts or [],
            review_instructions=review_instructions or [],
            context=context or {}
        )

        response = cp.wait_for_approval()

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
    ) -> HITLResponse:
        """
        Execute a checkpoint and exit if not approved.

        This is a convenience method for checkpoints where denial
        should halt execution entirely.

        Args:
            name: Unique identifier for this checkpoint
            description: Human-readable description
            **kwargs: Additional checkpoint arguments

        Returns:
            HITLResponse (only if approved)

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

    def get_history(self) -> list[dict]:
        """Get the checkpoint history."""
        return self.checkpoints.copy()

    def clear_history(self) -> None:
        """Clear the checkpoint history."""
        self.checkpoints = []
        self._save_history()

    def was_checkpoint_approved(self, name: str) -> Optional[bool]:
        """
        Check if a specific checkpoint was previously approved.

        Args:
            name: The checkpoint name to check

        Returns:
            True if approved, False if denied, None if not found
        """
        for cp in reversed(self.checkpoints):
            if cp["name"] == name:
                decision = cp.get("response", {}).get("decision")
                if decision:
                    return decision in ("approve", "amend")
        return None


# Global manager instance
_manager: Optional[HITLManager] = None


def get_manager() -> HITLManager:
    """Get or create the global HITL manager."""
    global _manager
    if _manager is None:
        _manager = HITLManager()
    return _manager


def reset_manager() -> None:
    """Reset the global HITL manager (useful for testing)."""
    global _manager
    _manager = None
