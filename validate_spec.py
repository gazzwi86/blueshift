#!/usr/bin/env python3
"""
App Specification Validator
===========================

Validates that app_spec.txt contains all required sections with sufficient detail
before running the agent. Run this as part of preflight checks.

Usage:
    python validate_spec.py [path/to/app_spec.txt]

    If no path provided, defaults to project_context/app_spec.txt
"""

import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.validation import AppSpecValidator, ValidationResult


def print_validation_report(result: ValidationResult, spec_path: str) -> None:
    """Print a formatted validation report."""
    print("\n" + "=" * 60)
    print("App Specification Validation Report")
    print("=" * 60)
    print(f"\nFile: {spec_path}")
    print(f"Valid: {'✓ YES' if result.is_valid else '✗ NO'}")

    if result.issues:
        print(f"\nIssues Found: {len(result.issues)}")
        print("-" * 40)
        for i, issue in enumerate(result.issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("\n✓ No issues found - specification is complete")

    # Summary of what was checked
    print("\n" + "-" * 40)
    print("Sections Validated:")
    print("  - project_name / overview")
    print("  - technology_stack (agent_framework, ai_models, etc.)")
    print("  - testing_strategy")
    print("  - data_sources / data_schema")
    print("  - guardrails / error_handling")
    print("  - agent_tools")
    print("  - infrastructure")
    print("  - evaluation_test_cases")
    print("=" * 60 + "\n")


def main():
    # Default path or command-line argument
    if len(sys.argv) > 1:
        spec_path = sys.argv[1]
    else:
        spec_path = "project_context/app_spec.txt"

    # Check file exists
    if not Path(spec_path).exists():
        print(f"Error: File not found: {spec_path}")
        print("\nUsage: python validate_spec.py [path/to/app_spec.txt]")
        sys.exit(1)

    # Validate
    validator = AppSpecValidator()
    result = validator.validate(spec_path)

    # Print report
    print_validation_report(result, spec_path)

    # Exit with appropriate code
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
