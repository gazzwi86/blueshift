"""
Feature List Synchronization

Syncs feature_list.json when app_spec.txt changes:
- Adds new features with passes: false
- Marks removed features as deprecated: true
- Never auto-passes or deletes features
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set


def extract_requirements_from_spec(spec_content: str) -> Set[str]:
    """
    Extract requirement identifiers from app_spec.txt.

    Looks for patterns like:
    - <requirement>...</requirement> tags
    - Feature: ... lines
    - Numbered requirements (1. ... 2. ...)

    Returns set of normalized requirement strings.
    """
    requirements = set()

    # Extract from requirement tags
    tag_pattern = r'<(\w+)>([^<]+)</\1>'
    for match in re.finditer(tag_pattern, spec_content, re.IGNORECASE):
        tag_name = match.group(1).lower()
        content = match.group(2).strip()
        if tag_name in ['requirement', 'feature', 'capability']:
            requirements.add(content[:100])  # Truncate long content

    # Extract from feature: lines
    feature_pattern = r'(?:feature|requirement|capability):\s*(.+?)(?:\n|$)'
    for match in re.finditer(feature_pattern, spec_content, re.IGNORECASE):
        requirements.add(match.group(1).strip()[:100])

    return requirements


def sync_features(
    project_dir: str | Path,
    dry_run: bool = False
) -> Dict[str, List[str]]:
    """
    Synchronize feature_list.json with app_spec.txt changes.

    Args:
        project_dir: Path to project directory
        dry_run: If True, report changes without modifying files

    Returns:
        Dict with keys: 'added', 'deprecated', 'unchanged'
    """
    project_path = Path(project_dir)
    feature_list_path = project_path / "feature_list.json"
    app_spec_path = project_path / "app_spec.txt"

    result = {
        'added': [],
        'deprecated': [],
        'unchanged': [],
        'errors': []
    }

    # Check files exist
    if not feature_list_path.exists():
        result['errors'].append("feature_list.json not found")
        return result

    if not app_spec_path.exists():
        result['errors'].append("app_spec.txt not found")
        return result

    # Load current feature list
    try:
        with open(feature_list_path) as f:
            feature_data = json.load(f)
    except json.JSONDecodeError as e:
        result['errors'].append(f"Invalid JSON in feature_list.json: {e}")
        return result

    # Extract existing feature titles
    existing_titles = {
        f.get('title', '').lower(): f
        for f in feature_data.get('features', [])
    }

    # Read and parse spec
    spec_content = app_spec_path.read_text()
    spec_requirements = extract_requirements_from_spec(spec_content)

    # Compare and sync
    features = feature_data.get('features', [])
    max_id = max(
        (int(f.get('id', 'feat_0').replace('feat_', ''))
         for f in features if f.get('id')),
        default=0
    )

    # Mark features not in spec as deprecated
    spec_titles_lower = {r.lower() for r in spec_requirements}
    for feature in features:
        title = feature.get('title', '').lower()
        if title and title not in spec_titles_lower:
            if not feature.get('deprecated'):
                feature['deprecated'] = True
                feature['deprecated_at'] = datetime.now().isoformat()
                feature['deprecated_reason'] = "Not found in current app_spec.txt"
                result['deprecated'].append(feature.get('title', 'unknown'))
            else:
                result['unchanged'].append(feature.get('title', 'unknown'))
        else:
            result['unchanged'].append(feature.get('title', 'unknown'))

    # Add new features from spec (not in existing list)
    for req in spec_requirements:
        if req.lower() not in existing_titles:
            max_id += 1
            new_feature = {
                'id': f'feat_{max_id:03d}',
                'title': req,
                'category': 'new_from_spec',
                'passes': False,  # ALWAYS false for new features
                'dod_checklist': {
                    'code_complete': False,
                    'unit_tests_pass': False,
                    'integration_tests_pass': False,
                    'deployed': False,
                    'smoke_tests_pass': False
                },
                'added_at': datetime.now().isoformat(),
                'added_reason': "Found in app_spec.txt during sync"
            }
            features.append(new_feature)
            result['added'].append(req)

    # Update total count
    feature_data['features'] = features
    feature_data['total_features'] = len([f for f in features if not f.get('deprecated')])
    feature_data['last_sync'] = datetime.now().isoformat()

    # Write back if not dry run
    if not dry_run and (result['added'] or result['deprecated']):
        # Backup original
        backup_path = feature_list_path.with_suffix('.json.backup')
        import shutil
        shutil.copy(feature_list_path, backup_path)

        # Write updated
        with open(feature_list_path, 'w') as f:
            json.dump(feature_data, f, indent=2)

    return result


def print_sync_report(result: Dict[str, List[str]]) -> None:
    """Print a human-readable sync report."""
    print("\n" + "=" * 60)
    print("  FEATURE LIST SYNC REPORT")
    print("=" * 60)

    if result['errors']:
        print(f"\nERRORS ({len(result['errors'])}):")
        for err in result['errors']:
            print(f"  - {err}")
        return

    print(f"\nAdded ({len(result['added'])}):")
    for item in result['added'][:10]:
        print(f"  + {item}")
    if len(result['added']) > 10:
        print(f"  ... and {len(result['added']) - 10} more")

    print(f"\nDeprecated ({len(result['deprecated'])}):")
    for item in result['deprecated'][:10]:
        print(f"  - {item}")
    if len(result['deprecated']) > 10:
        print(f"  ... and {len(result['deprecated']) - 10} more")

    print(f"\nUnchanged: {len(result['unchanged'])}")
    print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python feature_sync.py <project_dir> [--dry-run]")
        sys.exit(1)

    project_dir = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("DRY RUN - no changes will be made")

    result = sync_features(project_dir, dry_run=dry_run)
    print_sync_report(result)
