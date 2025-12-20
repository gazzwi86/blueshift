"""
Human-in-the-Loop (HITL) System
===============================

Provides interactive checkpoints where agent execution pauses
for human approval, denial, or feedback.

Usage:
    from lib.hitl import checkpoint, HITLDecision, HITLResponse

    result = checkpoint(
        name="initializer_complete",
        description="Review generated test fixtures",
        artifacts=["feature_list.json", "fixtures/"],
        review_instructions=["Check test coverage", "Verify data quality"]
    )

    if result.approved:
        continue_execution()
    else:
        halt_with_reason(result.denial_reason)
"""

from .types import HITLDecision, HITLResponse
from .checkpoint import HITLCheckpoint, checkpoint, require_approval
from .manager import HITLManager, get_manager

__all__ = [
    # Types
    "HITLDecision",
    "HITLResponse",
    # Checkpoint
    "HITLCheckpoint",
    "checkpoint",
    "require_approval",
    # Manager
    "HITLManager",
    "get_manager",
]
