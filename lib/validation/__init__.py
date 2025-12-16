"""
App Specification Validation
============================

Validates that app_spec.txt contains all required sections with sufficient detail
before the agent starts. This ensures all research and planning is done upfront,
eliminating the need for runtime web searches.
"""

from .app_spec import AppSpecValidator, ValidationResult

__all__ = ["AppSpecValidator", "ValidationResult"]
