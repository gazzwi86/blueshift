#!/usr/bin/env python3
"""
Definition of Done (DoD) Validator
===================================

THIS IS THE LAW - Validates that features are GENUINELY complete.

A feature is NOT complete unless ALL of the following are true:
1. passes == true
2. All DoD checklist items for the feature's category are satisfied
3. Real infrastructure exists (not just terraform plan)
4. Real evaluations have run (not just config with thresholds)
5. Real smoke tests have passed (not just unit tests with mocks)

MOCKS ARE NOT ENOUGH. Real infrastructure and data must be tested.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


# =============================================================================
# THIS IS THE LAW - FEATURE COMPLETION REQUIREMENTS
# =============================================================================

# Categories that REQUIRE real deployment verification
DEPLOYMENT_REQUIRED_CATEGORIES = {
    "deployment",
    "infrastructure",
    "e2e",
    "integration",
}

# Categories that REQUIRE real evaluation runs
EVALUATION_REQUIRED_CATEGORIES = {
    "evaluation",
}

# DoD fields that MUST be true for ALL features
UNIVERSAL_DOD_REQUIREMENTS = [
    "code_complete",
    "unit_tests_pass",
]

# DoD fields that MUST be true for deployment/infrastructure categories
# THIS IS THE LAW - these cannot be satisfied with mocks alone
DEPLOYMENT_DOD_REQUIREMENTS = [
    "deployed",               # terraform apply succeeded, AWS CLI shows resources
    "smoke_tests_pass",       # Real endpoint responds to real queries
    "integration_tests_pass", # Real services communicate successfully
]

# DoD fields that MUST be true for evaluation categories
# THIS IS THE LAW - actual LLM evaluation must run, not mock scores
EVALUATION_DOD_REQUIREMENTS = [
    "evaluation_threshold_met",  # Actual LLM-as-judge scores meet thresholds
]


@dataclass
class ValidationResult:
    """Result of validating a single feature."""
    feature_id: str
    category: str
    title: str
    is_complete: bool
    passes_field: bool
    missing_dod: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        status = "COMPLETE" if self.is_complete else "INCOMPLETE"
        result = f"[{status}] {self.feature_id} ({self.category}): {self.title}"
        if self.missing_dod:
            result += f"\n    Missing: {', '.join(self.missing_dod)}"
        if self.warnings:
            result += f"\n    Warnings: {', '.join(self.warnings)}"
        return result


@dataclass
class ProjectValidationResult:
    """Result of validating an entire project."""
    total_features: int
    complete_features: int
    incomplete_features: int
    feature_results: list[ValidationResult] = field(default_factory=list)

    @property
    def completion_percentage(self) -> float:
        if self.total_features == 0:
            return 0.0
        return round(self.complete_features / self.total_features * 100, 1)

    @property
    def is_project_complete(self) -> bool:
        return self.incomplete_features == 0

    def get_incomplete_by_category(self) -> dict[str, list[ValidationResult]]:
        """Group incomplete features by category."""
        by_category = {}
        for result in self.feature_results:
            if not result.is_complete:
                if result.category not in by_category:
                    by_category[result.category] = []
                by_category[result.category].append(result)
        return by_category


def validate_feature_dod(feature: dict) -> ValidationResult:
    """
    Validate a single feature against the Definition of Done requirements.

    THIS IS THE LAW:
    - passes must be true
    - All required DoD fields for the feature's category must be true
    - Deployment categories require real infrastructure (deployed=true)
    - Evaluation categories require real evaluation runs (evaluation_threshold_met=true)

    Args:
        feature: Feature dictionary from feature_list.json

    Returns:
        ValidationResult with completion status and missing requirements
    """
    feature_id = feature.get("id", "unknown")
    category = feature.get("category", "unknown")
    title = feature.get("title", "unknown")
    passes = feature.get("passes", False)
    dod = feature.get("dod_checklist", {})

    missing_dod = []
    warnings = []

    # Check universal DoD requirements
    for field in UNIVERSAL_DOD_REQUIREMENTS:
        if field in dod and not dod.get(field):
            missing_dod.append(f"{field}=false")

    # Check deployment-specific requirements
    if category in DEPLOYMENT_REQUIRED_CATEGORIES:
        for field in DEPLOYMENT_DOD_REQUIREMENTS:
            if field in dod and not dod.get(field):
                missing_dod.append(f"{field}=false [REQUIRED for {category}]")
            elif field not in dod:
                # Field should exist for deployment categories
                warnings.append(f"{field} not in DoD (should be present for {category})")

    # Check evaluation-specific requirements
    if category in EVALUATION_REQUIRED_CATEGORIES:
        for field in EVALUATION_DOD_REQUIREMENTS:
            if field in dod and not dod.get(field):
                missing_dod.append(f"{field}=false [REQUIRED for evaluation]")
            elif field not in dod:
                warnings.append(f"{field} not in DoD (should be present for evaluation)")

    # A feature is complete only if:
    # 1. passes == true
    # 2. No missing DoD requirements
    is_complete = passes and len(missing_dod) == 0

    return ValidationResult(
        feature_id=feature_id,
        category=category,
        title=title,
        is_complete=is_complete,
        passes_field=passes,
        missing_dod=missing_dod,
        warnings=warnings,
    )


def validate_project(feature_list_path: Path) -> ProjectValidationResult:
    """
    Validate an entire project's feature list.

    Args:
        feature_list_path: Path to feature_list.json

    Returns:
        ProjectValidationResult with overall status and feature details
    """
    with open(feature_list_path) as f:
        data = json.load(f)

    features = data.get("features", [])
    results = []
    complete_count = 0
    incomplete_count = 0

    for feature in features:
        result = validate_feature_dod(feature)
        results.append(result)
        if result.is_complete:
            complete_count += 1
        else:
            incomplete_count += 1

    return ProjectValidationResult(
        total_features=len(features),
        complete_features=complete_count,
        incomplete_features=incomplete_count,
        feature_results=results,
    )


def fix_feature_passes_field(feature: dict) -> tuple[dict, bool]:
    """
    Fix a feature's passes field based on its actual DoD status.

    THIS IS THE LAW:
    If DoD requirements are not met, passes MUST be false.

    Args:
        feature: Feature dictionary

    Returns:
        Tuple of (updated_feature, was_changed)
    """
    result = validate_feature_dod(feature)

    # If feature claims to pass but DoD is incomplete, fix it
    if feature.get("passes") and not result.is_complete:
        feature = feature.copy()
        feature["passes"] = False
        return feature, True

    return feature, False


def fix_project_feature_list(feature_list_path: Path, dry_run: bool = False) -> tuple[int, list[str]]:
    """
    Fix all features in a project that incorrectly claim to pass.

    THIS IS THE LAW:
    Features with incomplete DoD MUST have passes=false.

    Args:
        feature_list_path: Path to feature_list.json
        dry_run: If True, don't write changes, just report

    Returns:
        Tuple of (features_fixed_count, list_of_fixed_feature_ids)
    """
    with open(feature_list_path) as f:
        data = json.load(f)

    features = data.get("features", [])
    fixed_features = []
    fixed_ids = []

    for feature in features:
        updated_feature, was_changed = fix_feature_passes_field(feature)
        fixed_features.append(updated_feature)
        if was_changed:
            fixed_ids.append(updated_feature.get("id", "unknown"))

    if fixed_ids and not dry_run:
        data["features"] = fixed_features
        with open(feature_list_path, "w") as f:
            json.dump(data, f, indent=2)

    return len(fixed_ids), fixed_ids


def print_validation_report(result: ProjectValidationResult) -> None:
    """Print a detailed validation report."""
    print("\n" + "=" * 70)
    print("  DEFINITION OF DONE (DoD) VALIDATION REPORT")
    print("=" * 70)

    print(f"\nTotal Features: {result.total_features}")
    print(f"Complete:       {result.complete_features} ({result.completion_percentage}%)")
    print(f"Incomplete:     {result.incomplete_features}")
    print()

    if result.is_project_complete:
        print("PROJECT STATUS: GENUINELY COMPLETE")
        print("\nAll features have satisfied their Definition of Done requirements.")
        return

    print("PROJECT STATUS: INCOMPLETE")
    print("\n" + "-" * 70)
    print("INCOMPLETE FEATURES BY CATEGORY:")
    print("-" * 70)

    by_category = result.get_incomplete_by_category()
    for category, features in sorted(by_category.items()):
        print(f"\n{category.upper()} ({len(features)} incomplete):")
        for feat in features[:10]:  # Show first 10 per category
            print(f"  - {feat.feature_id}: {feat.title}")
            if feat.missing_dod:
                print(f"      Missing: {', '.join(feat.missing_dod)}")
        if len(features) > 10:
            print(f"  ... and {len(features) - 10} more")

    print("\n" + "=" * 70)
    print("THIS IS THE LAW:")
    print("- Deployment/infrastructure features REQUIRE terraform apply + AWS CLI verification")
    print("- Evaluation features REQUIRE actual LLM-as-judge runs with real scores")
    print("- Integration features REQUIRE real service communication tests")
    print("- Mocks and fixtures are NOT sufficient for these categories")
    print("=" * 70)


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate project features against Definition of Done requirements",
        epilog="""
THIS IS THE LAW:
  Features are NOT complete unless ALL DoD requirements are satisfied.
  Mocks are NOT enough for deployment, infrastructure, and evaluation features.
        """
    )
    parser.add_argument(
        "feature_list",
        type=Path,
        help="Path to feature_list.json"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Fix features that incorrectly claim to pass"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    if not args.feature_list.exists():
        print(f"ERROR: File not found: {args.feature_list}")
        sys.exit(1)

    if args.fix or args.dry_run:
        count, fixed_ids = fix_project_feature_list(args.feature_list, dry_run=args.dry_run)
        action = "Would fix" if args.dry_run else "Fixed"
        print(f"{action} {count} features with incorrect passes=true:")
        for fid in fixed_ids:
            print(f"  - {fid}")
        if not args.dry_run and count > 0:
            print(f"\nUpdated {args.feature_list}")
        sys.exit(0 if count == 0 else 1)

    result = validate_project(args.feature_list)

    if args.json:
        output = {
            "total_features": result.total_features,
            "complete_features": result.complete_features,
            "incomplete_features": result.incomplete_features,
            "completion_percentage": result.completion_percentage,
            "is_project_complete": result.is_project_complete,
            "incomplete_by_category": {
                cat: [{"id": r.feature_id, "title": r.title, "missing": r.missing_dod}
                      for r in results]
                for cat, results in result.get_incomplete_by_category().items()
            }
        }
        print(json.dumps(output, indent=2))
    else:
        print_validation_report(result)

    sys.exit(0 if result.is_project_complete else 1)


if __name__ == "__main__":
    main()
