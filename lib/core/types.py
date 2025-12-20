"""
Common Types
============

Shared type definitions and dataclasses used throughout the harness.
Uses frozen dataclasses for immutability (functional programming style).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class SessionStatus(Enum):
    """Status of an agent session."""
    CONTINUE = "continue"  # Session completed, should continue to next
    STOP = "stop"          # Project complete, stop the loop
    ERROR = "error"        # Session encountered an error
    HITL = "hitl"          # Waiting for human-in-the-loop approval


class ValidationLevel(Enum):
    """Severity level for validation results."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class ValidationResult:
    """
    Result of a validation check.

    Immutable for functional programming patterns.
    """
    passed: bool
    message: str
    level: ValidationLevel = ValidationLevel.INFO
    details: Optional[dict] = None

    def __str__(self) -> str:
        prefix = {
            ValidationLevel.ERROR: "[ERROR]",
            ValidationLevel.WARNING: "[WARN]",
            ValidationLevel.INFO: "[INFO]",
        }[self.level]
        return f"{prefix} {self.message}"


@dataclass(frozen=True)
class FeatureStatus:
    """
    Status of a single feature from feature_list.json.

    Immutable snapshot of feature state.
    """
    id: str
    title: str
    category: str
    passes: bool
    dod_complete: bool = False
    blocked_by: Optional[str] = None
    block_reason: Optional[str] = None


@dataclass(frozen=True)
class ProgressSnapshot:
    """
    Immutable snapshot of project progress.

    Used for displaying progress summaries.
    """
    total_features: int
    passing_features: int
    categories: dict[str, tuple[int, int]]  # category -> (passing, total)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def completion_percentage(self) -> float:
        if self.total_features == 0:
            return 0.0
        return (self.passing_features / self.total_features) * 100

    @property
    def is_complete(self) -> bool:
        return self.passing_features == self.total_features and self.total_features > 0


@dataclass(frozen=True)
class VerificationResult:
    """
    Result of post-session verification.

    Immutable record of what was verified.
    """
    passed: bool
    reason: str
    exit_code: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    details: Optional[dict] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "reason": self.reason,
            "exit_code": self.exit_code,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }
