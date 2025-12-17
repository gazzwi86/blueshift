#!/usr/bin/env python3
"""
Post-Initialization Validation
==============================

Validates the artifacts created by the initializer agent before approving
the HITL checkpoint. Run this after Session 1 completes.

Checks:
1. feature_list.json exists and has valid schema
2. Required categories are present (including 'deployment')
3. Minimum feature count (200+)
4. DoR/DoD checklists are present
5. testing_strategy.md exists
6. workflow_phases.md exists with deployment phases

Usage:
    python post_init_validation.py <project_dir>

Example:
    python post_init_validation.py generations/pixieops_v2
"""

import json
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.validation import validate_feature_list, print_validation_report


# Required categories that MUST be present
REQUIRED_CATEGORIES = {
    "test_setup",
    "credential_validation",
    "tech_stack",
    "infrastructure",
    "deployment",  # CRITICAL - must have deployment tests
}

# Minimum feature count
MIN_FEATURES = 150  # Allow some flexibility, but warn below 200

# Required files
REQUIRED_FILES = [
    "feature_list.json",
    "testing_strategy.md",
    "workflow_phases.md",
    "credentials.py",
    "init.sh",
]


def validate_feature_count_and_categories(feature_list_path: Path) -> tuple[bool, list[str]]:
    """Validate feature count and category distribution."""
    issues = []

    with open(feature_list_path) as f:
        features = json.load(f)

    # Count features
    total = len(features)
    if total < MIN_FEATURES:
        issues.append(f"Only {total} features found. Expected {MIN_FEATURES}+ for comprehensive coverage.")
    elif total < 200:
        issues.append(f"Warning: {total} features found. Recommended 200+ for thorough testing.")

    # Count by category
    categories = {}
    for f in features:
        cat = f.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    # Check required categories
    missing = REQUIRED_CATEGORIES - set(categories.keys())
    if missing:
        issues.append(f"Missing required categories: {missing}")

    # Check deployment category specifically
    if "deployment" not in categories:
        issues.append(
            "CRITICAL: No 'deployment' category found! "
            "Agent will not deploy infrastructure or agent code."
        )
    elif categories["deployment"] < 5:
        issues.append(
            f"Only {categories['deployment']} deployment tests. "
            "Should have at least 5 (terraform apply, resource verification, agent deploy, smoke tests)."
        )

    # Print category summary
    print("\nFeature Categories:")
    print("-" * 40)
    for cat, count in sorted(categories.items()):
        marker = "✓" if cat in REQUIRED_CATEGORIES else " "
        warning = " ⚠️" if cat in REQUIRED_CATEGORIES and count < 5 else ""
        print(f"  {marker} {cat}: {count}{warning}")

    print(f"\nTotal: {total} features")

    return len(issues) == 0, issues


def validate_dor_dod_structure(feature_list_path: Path) -> tuple[bool, list[str]]:
    """Check if features have DoR/DoD checklists."""
    issues = []

    with open(feature_list_path) as f:
        features = json.load(f)

    # Sample check - look at first 10 features
    features_with_dor = 0
    features_with_dod = 0
    features_with_ac = 0

    for f in features[:20]:  # Check first 20
        if "dor_checklist" in f:
            features_with_dor += 1
        if "dod_checklist" in f:
            features_with_dod += 1
        if "acceptance_criteria" in f and len(f["acceptance_criteria"]) > 0:
            features_with_ac += 1

    sample_size = min(20, len(features))

    print("\nQuality Framework Adoption (sampled):")
    print("-" * 40)
    print(f"  Features with DoR checklist: {features_with_dor}/{sample_size}")
    print(f"  Features with DoD checklist: {features_with_dod}/{sample_size}")
    print(f"  Features with acceptance criteria: {features_with_ac}/{sample_size}")

    # Warn if quality framework not adopted
    if features_with_dor < sample_size * 0.5:
        issues.append(
            f"Warning: Only {features_with_dor}/{sample_size} features have DoR checklist. "
            "Quality framework may not be fully adopted."
        )
    if features_with_ac < sample_size * 0.5:
        issues.append(
            f"Warning: Only {features_with_ac}/{sample_size} features have acceptance criteria. "
            "Consider adding Given/When/Then criteria for better testability."
        )

    return len([i for i in issues if not i.startswith("Warning")]) == 0, issues


def validate_workflow_phases(project_dir: Path) -> tuple[bool, list[str]]:
    """Check workflow_phases.md for deployment phases."""
    issues = []
    workflow_path = project_dir / "workflow_phases.md"

    if not workflow_path.exists():
        return False, ["workflow_phases.md not found"]

    content = workflow_path.read_text().lower()

    # Check for deployment phases
    if "infrastructure deployment" not in content and "terraform apply" not in content:
        issues.append(
            "Warning: workflow_phases.md may not include Infrastructure Deployment phase. "
            "Agent may not run terraform apply."
        )

    if "agent deployment" not in content and "agentcore deploy" not in content:
        issues.append(
            "Warning: workflow_phases.md may not include Agent Deployment phase. "
            "Agent may not deploy to AgentCore."
        )

    # Check phase count
    phase_count = content.count("## phase")
    print(f"\nWorkflow Phases: {phase_count} phases defined")

    return len([i for i in issues if not i.startswith("Warning")]) == 0, issues


def check_required_files(project_dir: Path) -> tuple[bool, list[str]]:
    """Check all required files exist."""
    issues = []

    print("\nRequired Files:")
    print("-" * 40)

    for filename in REQUIRED_FILES:
        path = project_dir / filename
        exists = path.exists()
        marker = "✓" if exists else "✗"
        print(f"  {marker} {filename}")
        if not exists:
            issues.append(f"Missing required file: {filename}")

    # Check fixtures directory
    fixtures_dir = project_dir / "fixtures"
    if fixtures_dir.exists():
        fixture_count = len(list(fixtures_dir.glob("*.json")))
        print(f"  ✓ fixtures/ ({fixture_count} JSON files)")
    else:
        print("  ✗ fixtures/")
        issues.append("Missing fixtures directory")

    return len(issues) == 0, issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python post_init_validation.py <project_dir>")
        print("Example: python post_init_validation.py generations/pixieops_v2")
        sys.exit(1)

    project_dir = Path(sys.argv[1])

    if not project_dir.exists():
        print(f"Error: Project directory not found: {project_dir}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Post-Initialization Validation")
    print("=" * 60)
    print(f"\nProject: {project_dir}")

    all_issues = []
    all_valid = True

    # 1. Check required files
    valid, issues = check_required_files(project_dir)
    all_valid = all_valid and valid
    all_issues.extend(issues)

    feature_list_path = project_dir / "feature_list.json"
    if not feature_list_path.exists():
        print("\n✗ Cannot continue without feature_list.json")
        sys.exit(1)

    # 2. Validate feature_list.json schema
    print("\n" + "-" * 40)
    print("Feature List Schema Validation")
    print("-" * 40)
    valid, schema_errors = validate_feature_list(feature_list_path)
    if schema_errors:
        error_count = sum(1 for e in schema_errors if e.severity == "error")
        warning_count = sum(1 for e in schema_errors if e.severity == "warning")
        print(f"  Schema errors: {error_count}")
        print(f"  Schema warnings: {warning_count}")
        if error_count > 0:
            all_valid = False
            all_issues.append(f"Feature list has {error_count} schema errors")
    else:
        print("  ✓ Schema valid")

    # 3. Validate feature count and categories
    valid, issues = validate_feature_count_and_categories(feature_list_path)
    all_valid = all_valid and valid
    all_issues.extend(issues)

    # 4. Check DoR/DoD structure
    valid, issues = validate_dor_dod_structure(feature_list_path)
    # Don't fail on DoR/DoD warnings, just report
    all_issues.extend(issues)

    # 5. Check workflow phases
    valid, issues = validate_workflow_phases(project_dir)
    all_issues.extend(issues)

    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    errors = [i for i in all_issues if not i.startswith("Warning")]
    warnings = [i for i in all_issues if i.startswith("Warning")]

    if errors:
        print(f"\n✗ ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")

    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")

    if all_valid and not errors:
        print("\n✓ Validation PASSED - Safe to approve HITL checkpoint")
    else:
        print("\n✗ Validation FAILED - Review issues before approving")

    print("=" * 60 + "\n")

    sys.exit(0 if (all_valid and not errors) else 1)


if __name__ == "__main__":
    main()
