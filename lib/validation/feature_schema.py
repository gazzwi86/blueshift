"""
Feature List JSON Schema Validation
====================================

Validates feature_list.json against the enhanced schema with DoR/DoD requirements.
"""

import json
from pathlib import Path
from typing import Optional


FEATURE_SCHEMA = {
    "type": "object",
    "required": [
        "id", "category", "title", "description",
        "acceptance_criteria", "test_approach",
        "dor_checklist", "dod_checklist", "passes"
    ],
    "properties": {
        "id": {
            "type": "string",
            "pattern": r"^[a-z_]+_[0-9]+$",
            "description": "Unique identifier (e.g., feat_001, deploy_003)"
        },
        "category": {
            "type": "string",
            "enum": [
                "test_setup", "credential_validation", "tech_stack",
                "infrastructure", "deployment", "core_behavior",
                "integration", "error_handling", "guardrails",
                "evaluation", "e2e", "slack_integration"
            ]
        },
        "title": {
            "type": "string",
            "minLength": 5,
            "maxLength": 100
        },
        "description": {
            "type": "string",
            "minLength": 20
        },
        "business_value": {
            "type": "string",
            "description": "Optional but recommended"
        },
        "acceptance_criteria": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["id", "then"],
                "properties": {
                    "id": {"type": "string"},
                    "given": {"type": "string"},
                    "when": {"type": "string"},
                    "then": {"type": "string"}
                }
            }
        },
        "test_approach": {
            "type": "object",
            "required": ["test_types", "assertions"],
            "properties": {
                "test_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["unit", "integration", "e2e", "evaluation", "manual"]
                    },
                    "minItems": 1
                },
                "fixtures": {"type": "array", "items": {"type": "string"}},
                "mocks": {"type": "array", "items": {"type": "string"}},
                "assertions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1
                }
            }
        },
        "dependencies": {
            "type": "object",
            "properties": {
                "features": {"type": "array", "items": {"type": "string"}},
                "infrastructure": {"type": "array", "items": {"type": "string"}},
                "credentials": {"type": "array", "items": {"type": "string"}}
            }
        },
        "dor_checklist": {
            "type": "object",
            "required": [
                "clear_description",
                "acceptance_criteria",
                "test_approach",
                "dependencies_resolved",
                "tech_aligned"
            ],
            "properties": {
                "clear_description": {"type": "boolean"},
                "acceptance_criteria": {"type": "boolean"},
                "test_approach": {"type": "boolean"},
                "dependencies_resolved": {"type": "boolean"},
                "tech_aligned": {"type": "boolean"}
            }
        },
        "dod_checklist": {
            "type": "object",
            "required": [
                "code_complete",
                "unit_tests_pass",
                "coverage_threshold_met"
            ],
            "properties": {
                "code_complete": {"type": "boolean"},
                "unit_tests_pass": {"type": "boolean"},
                "coverage_threshold_met": {"type": "boolean"},
                "integration_tests_pass": {"type": "boolean"},
                "evaluation_threshold_met": {"type": "boolean"},
                "deployed": {"type": "boolean"},
                "smoke_tests_pass": {"type": "boolean"},
                "ci_passes": {"type": "boolean"},
                "documented": {"type": "boolean"}
            }
        },
        "coverage": {
            "type": "object",
            "properties": {
                "target": {"type": "number", "minimum": 0, "maximum": 100},
                "actual": {"type": ["number", "null"]}
            }
        },
        "evaluation_scores": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "threshold": {"type": "number", "minimum": 0, "maximum": 1},
                    "actual": {"type": ["number", "null"]}
                }
            }
        },
        "passes": {
            "type": "boolean"
        }
    }
}


class ValidationError:
    """Represents a validation error."""

    def __init__(self, feature_id: str, field: str, message: str, severity: str = "error"):
        self.feature_id = feature_id
        self.field = field
        self.message = message
        self.severity = severity  # "error" or "warning"

    def __str__(self):
        return f"[{self.severity.upper()}] {self.feature_id}.{self.field}: {self.message}"


def validate_feature(feature: dict, index: int) -> list[ValidationError]:
    """
    Validate a single feature against the schema.

    Args:
        feature: Feature dictionary
        index: Index in the feature list (for error messages)

    Returns:
        List of validation errors
    """
    errors = []
    feature_id = feature.get("id", f"feature[{index}]")

    # Required fields
    required = ["id", "category", "title", "description",
                "acceptance_criteria", "test_approach",
                "dor_checklist", "dod_checklist", "passes"]

    for field in required:
        if field not in feature:
            errors.append(ValidationError(feature_id, field, f"Missing required field: {field}"))

    # ID format
    if "id" in feature:
        import re
        if not re.match(r"^[a-z_]+_[0-9]+$", feature["id"]):
            errors.append(ValidationError(
                feature_id, "id",
                f"Invalid ID format '{feature['id']}'. Expected pattern: category_number (e.g., feat_001)"
            ))

    # Category validation
    valid_categories = [
        "test_setup", "credential_validation", "tech_stack",
        "infrastructure", "deployment", "core_behavior",
        "integration", "error_handling", "guardrails",
        "evaluation", "e2e", "slack_integration"
    ]
    if "category" in feature and feature["category"] not in valid_categories:
        errors.append(ValidationError(
            feature_id, "category",
            f"Invalid category '{feature['category']}'. Valid: {valid_categories}"
        ))

    # Title length
    if "title" in feature:
        if len(feature["title"]) < 5:
            errors.append(ValidationError(feature_id, "title", "Title too short (min 5 chars)"))
        if len(feature["title"]) > 100:
            errors.append(ValidationError(feature_id, "title", "Title too long (max 100 chars)"))

    # Description length
    if "description" in feature and len(feature["description"]) < 20:
        errors.append(ValidationError(
            feature_id, "description",
            "Description too short (min 20 chars). Be more specific."
        ))

    # Acceptance criteria
    if "acceptance_criteria" in feature:
        ac = feature["acceptance_criteria"]
        if not isinstance(ac, list) or len(ac) < 1:
            errors.append(ValidationError(
                feature_id, "acceptance_criteria",
                "Must have at least 1 acceptance criterion"
            ))
        else:
            for i, criterion in enumerate(ac):
                if "then" not in criterion:
                    errors.append(ValidationError(
                        feature_id, f"acceptance_criteria[{i}]",
                        "Each criterion must have a 'then' clause"
                    ))

    # Test approach
    if "test_approach" in feature:
        ta = feature["test_approach"]
        if "test_types" not in ta or not ta["test_types"]:
            errors.append(ValidationError(
                feature_id, "test_approach.test_types",
                "Must specify at least one test type"
            ))
        if "assertions" not in ta or not ta["assertions"]:
            errors.append(ValidationError(
                feature_id, "test_approach.assertions",
                "Must specify at least one assertion"
            ))

    # DoR checklist
    if "dor_checklist" in feature:
        dor = feature["dor_checklist"]
        dor_fields = ["clear_description", "acceptance_criteria", "test_approach",
                      "dependencies_resolved", "tech_aligned"]
        for field in dor_fields:
            if field not in dor:
                errors.append(ValidationError(
                    feature_id, f"dor_checklist.{field}",
                    f"Missing DoR field: {field}"
                ))

    # DoD checklist
    if "dod_checklist" in feature:
        dod = feature["dod_checklist"]
        dod_required = ["code_complete", "unit_tests_pass", "coverage_threshold_met"]
        for field in dod_required:
            if field not in dod:
                errors.append(ValidationError(
                    feature_id, f"dod_checklist.{field}",
                    f"Missing DoD field: {field}"
                ))

    # Business value (warning, not error)
    if "business_value" not in feature:
        errors.append(ValidationError(
            feature_id, "business_value",
            "Missing business_value - consider adding for INVEST compliance",
            severity="warning"
        ))

    return errors


def validate_feature_list(feature_list_path: Path) -> tuple[bool, list[ValidationError]]:
    """
    Validate an entire feature_list.json file.

    Args:
        feature_list_path: Path to feature_list.json

    Returns:
        Tuple of (is_valid, errors)
    """
    all_errors = []

    # Load file
    try:
        with open(feature_list_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [ValidationError("file", "json", f"Invalid JSON: {e}")]
    except FileNotFoundError:
        return False, [ValidationError("file", "path", f"File not found: {feature_list_path}")]

    # Check structure
    if not isinstance(data, list):
        return False, [ValidationError("file", "structure", "Root must be an array of features")]

    # Check minimum features
    if len(data) < 50:
        all_errors.append(ValidationError(
            "file", "count",
            f"Only {len(data)} features. Expected 200+ for comprehensive coverage.",
            severity="warning"
        ))

    # Validate each feature
    seen_ids = set()
    for i, feature in enumerate(data):
        # Check for duplicate IDs
        fid = feature.get("id", "")
        if fid in seen_ids:
            all_errors.append(ValidationError(fid, "id", f"Duplicate feature ID: {fid}"))
        seen_ids.add(fid)

        # Validate feature
        errors = validate_feature(feature, i)
        all_errors.extend(errors)

    # Check for required categories
    categories = {f.get("category") for f in data}
    required_categories = {"test_setup", "credential_validation", "deployment"}
    missing = required_categories - categories
    if missing:
        all_errors.append(ValidationError(
            "file", "categories",
            f"Missing required categories: {missing}",
            severity="warning"
        ))

    # Determine validity (errors only, warnings don't fail)
    errors_only = [e for e in all_errors if e.severity == "error"]
    is_valid = len(errors_only) == 0

    return is_valid, all_errors


def print_validation_report(errors: list[ValidationError]) -> None:
    """Print a formatted validation report."""
    if not errors:
        print("✓ Feature list validation passed - no issues found")
        return

    error_count = sum(1 for e in errors if e.severity == "error")
    warning_count = sum(1 for e in errors if e.severity == "warning")

    print(f"\nFeature List Validation Report")
    print("=" * 50)
    print(f"Errors: {error_count}")
    print(f"Warnings: {warning_count}")
    print()

    # Group by feature
    by_feature = {}
    for error in errors:
        if error.feature_id not in by_feature:
            by_feature[error.feature_id] = []
        by_feature[error.feature_id].append(error)

    for feature_id, feature_errors in by_feature.items():
        print(f"\n{feature_id}:")
        for error in feature_errors:
            prefix = "  ✗" if error.severity == "error" else "  ⚠"
            print(f"{prefix} {error.field}: {error.message}")

    if error_count > 0:
        print(f"\n✗ Validation FAILED with {error_count} errors")
    else:
        print(f"\n✓ Validation passed with {warning_count} warnings")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python feature_schema.py <path/to/feature_list.json>")
        sys.exit(1)

    path = Path(sys.argv[1])
    is_valid, errors = validate_feature_list(path)
    print_validation_report(errors)
    sys.exit(0 if is_valid else 1)
