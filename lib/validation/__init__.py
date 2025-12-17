"""
Validation Module
=================

Validates app_spec.txt and feature_list.json for completeness and correctness.
"""

from .app_spec import AppSpecValidator, ValidationResult
from .feature_schema import (
    validate_feature,
    validate_feature_list,
    print_validation_report,
    ValidationError,
)

__all__ = [
    # App spec validation
    "AppSpecValidator",
    "ValidationResult",
    # Feature list validation
    "validate_feature",
    "validate_feature_list",
    "print_validation_report",
    "ValidationError",
]
