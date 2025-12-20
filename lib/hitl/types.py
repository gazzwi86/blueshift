"""
HITL Type Definitions
=====================

Immutable types for the Human-in-the-Loop system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class HITLDecision(Enum):
    """Possible decisions from human reviewer."""
    APPROVE = "approve"
    DENY = "deny"
    AMEND = "amend"  # Approve with feedback/changes


@dataclass(frozen=True)
class HITLResponse:
    """
    Immutable response from human reviewer at a checkpoint.

    Uses frozen=True for functional programming patterns.
    """
    decision: HITLDecision
    feedback: Optional[str] = None
    denial_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def approved(self) -> bool:
        """Check if the checkpoint was approved (with or without amendments)."""
        return self.decision in (HITLDecision.APPROVE, HITLDecision.AMEND)

    @property
    def has_feedback(self) -> bool:
        """Check if feedback was provided."""
        return bool(self.feedback)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "decision": self.decision.value,
            "feedback": self.feedback,
            "denial_reason": self.denial_reason,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HITLResponse":
        """Create from dictionary."""
        return cls(
            decision=HITLDecision(data["decision"]),
            feedback=data.get("feedback"),
            denial_reason=data.get("denial_reason"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now()
        )


@dataclass(frozen=True)
class HITLCheckpointRecord:
    """
    Immutable record of a completed checkpoint.

    Used for history tracking.
    """
    name: str
    description: str
    response: HITLResponse
    artifacts: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "response": self.response.to_dict(),
            "artifacts": list(self.artifacts)
        }
