"""
Validation Module
=================

THIS IS THE LAW - Validation tools for the Blueshift harness.

Validates app_spec.txt, feature_list.json, and Definition of Done requirements.

CRITICAL: Mocks and fixtures are NOT sufficient for:
- deployment features (require terraform apply + AWS CLI)
- infrastructure features (require real AWS resources)
- evaluation features (require actual LLM-as-judge scores)
- integration features (require real service calls)
"""

from .app_spec import AppSpecValidator, ValidationResult as AppSpecValidationResult
from .feature_schema import (
    validate_feature,
    validate_feature_list,
    print_validation_report,
    ValidationError,
)
from .dod_validator import (
    validate_feature_dod,
    validate_project,
    fix_project_feature_list,
    ValidationResult as DoDValidationResult,
    ProjectValidationResult,
    DEPLOYMENT_REQUIRED_CATEGORIES,
    EVALUATION_REQUIRED_CATEGORIES,
    UNIVERSAL_DOD_REQUIREMENTS,
    DEPLOYMENT_DOD_REQUIREMENTS,
    EVALUATION_DOD_REQUIREMENTS,
)

__all__ = [
    # App spec validation
    "AppSpecValidator",
    "AppSpecValidationResult",
    # Feature list validation
    "validate_feature",
    "validate_feature_list",
    "print_validation_report",
    "ValidationError",
    # DoD validation - THIS IS THE LAW
    "validate_feature_dod",
    "validate_project",
    "fix_project_feature_list",
    "DoDValidationResult",
    "ProjectValidationResult",
    "DEPLOYMENT_REQUIRED_CATEGORIES",
    "EVALUATION_REQUIRED_CATEGORIES",
    "UNIVERSAL_DOD_REQUIREMENTS",
    "DEPLOYMENT_DOD_REQUIREMENTS",
    "EVALUATION_DOD_REQUIREMENTS",
]
