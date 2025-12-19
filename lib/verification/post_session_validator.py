#!/usr/bin/env python3
"""
Post-Session Validator
======================

THIS IS THE LAW - Runs after each agent session to verify claims.
The agent CANNOT bypass this verification.

This module is called by the harness (not the agent) to verify that:
1. Infrastructure is actually deployed (terraform plan shows no changes)
2. Agent is actually deployed and responding (agentcore status + invoke)
3. Evaluation scores actually exist and meet thresholds

The agent can claim whatever it wants in feature_list.json, but the harness
will overwrite those claims based on the results of this verification.

MOCKS ARE NOT SUFFICIENT. This runs real commands against real infrastructure.
"""

import subprocess
import json
import os
import re
import glob as glob_module
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple


def _get_aws_env(project_dir: Path) -> dict:
    """
    Get environment variables with AWS credentials.

    Loads from project .env file if AWS_PROFILE not already set.
    """
    env = os.environ.copy()

    # If AWS_PROFILE already set, use it
    if env.get("AWS_PROFILE"):
        return env

    # Try to load from project .env file
    env_file = project_dir / ".env"
    if env_file.exists():
        try:
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key.startswith("AWS_"):
                        env[key] = value
        except Exception:
            pass

    # Also check harness-level .env
    harness_env = Path(__file__).parent.parent.parent / ".env"
    if harness_env.exists():
        try:
            for line in harness_env.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key.startswith("AWS_") and key not in env:
                        env[key] = value
        except Exception:
            pass

    return env


# Try to import AI code analyzer (optional enhancement)
try:
    from .ai_code_analyzer import detect_placeholders_with_ai, quick_placeholder_check
    AI_ANALYZER_AVAILABLE = True
except ImportError:
    AI_ANALYZER_AVAILABLE = False

# Categories that require real deployment verification
DEPLOYMENT_CATEGORIES = {"deployment", "infrastructure", "e2e", "integration"}
EVALUATION_CATEGORY = "evaluation"

# Required evaluation metrics and their thresholds
REQUIRED_EVALUATION_METRICS = {
    "helpfulness": 0.70,
    "correctness": 0.70,
    "safety": 0.95,
    "tool_selection": 0.80,
    "goal_achievement": 0.70,
}

# Patterns that indicate placeholder/stub code
PLACEHOLDER_PATTERNS = [
    r'def lambda_handler.*:\s*return\s*\{["\']statusCode["\']\s*:\s*200\}',
    r'# TODO:?\s*implement',
    r'# PLACEHOLDER',
    r'raise NotImplementedError',
    r'pass\s*#\s*(?:TODO|FIXME|placeholder)',
    r'lambda_placeholder\.zip',
]

# Required lambda implementations (must have actual logic, not just placeholders)
# Supports multiple naming conventions - agent may use different directory names
REQUIRED_LAMBDA_IMPLEMENTATIONS = {
    "extractor": ["lambda-extractor", "sharepoint-extractor"],  # SharePoint extraction
    "processor": ["lambda-processor", "document-processor"],    # Document processing
}


def run_placeholder_detection(project_dir: Path, use_ai: bool = True) -> dict:
    """
    Detect placeholder/stub code in the project.

    THIS IS THE LAW:
    - Placeholder code is NOT acceptable for deployment features
    - Lambda functions MUST have actual implementation, not just return 200
    - Terraform modules that deploy placeholder zips are NOT complete

    Uses a hybrid approach:
    1. Pattern-based detection (fast, catches obvious placeholders)
    2. AI-powered analysis (robust, catches subtle placeholders) - if available

    Args:
        project_dir: Path to project directory
        use_ai: Whether to use AI-powered analysis (default: True)

    Returns:
        dict with 'passed', 'placeholders_found', 'reason', 'timestamp', 'ai_analysis'
    """
    placeholders_found = []
    ai_analysis_result = None

    # 1. Check Terraform modules for placeholder patterns
    tf_patterns = ["infra/**/*.tf"]
    for pattern in tf_patterns:
        for tf_file in project_dir.glob(pattern):
            try:
                content = tf_file.read_text()
                for placeholder_pattern in PLACEHOLDER_PATTERNS:
                    if re.search(placeholder_pattern, content, re.IGNORECASE | re.MULTILINE):
                        placeholders_found.append({
                            "file": str(tf_file.relative_to(project_dir)),
                            "type": "terraform",
                            "pattern": placeholder_pattern,
                            "issue": "Placeholder code detected in Terraform module"
                        })
            except Exception as e:
                pass  # Skip unreadable files

    # 2. Check for required Lambda implementations
    # Each lambda type can have multiple valid directory names
    for lambda_type, valid_names in REQUIRED_LAMBDA_IMPLEMENTATIONS.items():
        # Check infra modules for placeholder zips
        for lambda_name in valid_names:
            lambda_module_dir = project_dir / "infra" / "modules" / lambda_name
            if lambda_module_dir.exists():
                main_tf = lambda_module_dir / "main.tf"
                if main_tf.exists():
                    content = main_tf.read_text()
                    if "lambda_placeholder.zip" in content:
                        placeholders_found.append({
                            "file": str(main_tf.relative_to(project_dir)),
                            "type": "lambda_placeholder",
                            "lambda": lambda_name,
                            "issue": f"Lambda {lambda_name} deploys placeholder code instead of real implementation"
                        })

        # Check if at least one valid src implementation exists for this lambda type
        src_found = False
        for lambda_name in valid_names:
            src_lambda_dir = project_dir / "src" / "lambdas" / lambda_name
            if src_lambda_dir.exists():
                src_found = True
                break

        if not src_found:
            placeholders_found.append({
                "file": f"src/lambdas/[{' or '.join(valid_names)}]",
                "type": "missing_implementation",
                "lambda": lambda_type,
                "issue": f"Lambda {lambda_type} has no Python implementation (tried: {', '.join(valid_names)})"
            })

    # 3. Check Python source files for placeholder patterns
    py_patterns = ["src/**/*.py"]
    for pattern in py_patterns:
        for py_file in project_dir.glob(pattern):
            try:
                content = py_file.read_text()
                for placeholder_pattern in PLACEHOLDER_PATTERNS:
                    if re.search(placeholder_pattern, content, re.IGNORECASE | re.MULTILINE):
                        # Skip test files
                        if "/test" in str(py_file) or "_test.py" in str(py_file):
                            continue
                        placeholders_found.append({
                            "file": str(py_file.relative_to(project_dir)),
                            "type": "python_placeholder",
                            "pattern": placeholder_pattern,
                            "issue": "Placeholder code detected in source file"
                        })
            except Exception as e:
                pass  # Skip unreadable files

    # 4. Check if S3 buckets contain actual data (for data pipeline)
    # Note: This check is skipped if AWS credentials aren't available
    raw_docs_bucket_empty = True
    vectors_bucket_empty = True
    aws_env = _get_aws_env(project_dir)

    try:
        # Check raw docs bucket
        result = subprocess.run(
            ["aws", "s3", "ls", "s3://pixieops-raw-docs-dev/", "--recursive"],
            capture_output=True,
            text=True,
            timeout=30,
            env=aws_env
        )
        if result.returncode == 0 and result.stdout.strip():
            raw_docs_bucket_empty = False
    except Exception:
        pass

    try:
        # Check vectors bucket
        result = subprocess.run(
            ["aws", "s3", "ls", "s3://pixieops-bios-vectors-dev/", "--recursive"],
            capture_output=True,
            text=True,
            timeout=30,
            env=aws_env
        )
        if result.returncode == 0 and result.stdout.strip():
            vectors_bucket_empty = False
    except Exception:
        pass

    if raw_docs_bucket_empty:
        placeholders_found.append({
            "file": "s3://pixieops-raw-docs-dev/",
            "type": "empty_bucket",
            "issue": "Raw docs bucket is EMPTY - data pipeline has never run"
        })

    if vectors_bucket_empty:
        placeholders_found.append({
            "file": "s3://pixieops-bios-vectors-dev/",
            "type": "empty_bucket",
            "issue": "Vectors bucket is EMPTY - no embeddings have been generated"
        })

    # 5. AI-powered analysis (optional, more robust)
    if use_ai and AI_ANALYZER_AVAILABLE:
        try:
            ai_result = detect_placeholders_with_ai(project_dir, verbose=False)
            ai_analysis_result = ai_result.get("ai_analysis", {})

            # Add AI-detected placeholders to the list
            for ai_placeholder in ai_result.get("placeholders_found", []):
                # Check if we haven't already flagged this file
                existing_files = {p.get("file") for p in placeholders_found}
                if ai_placeholder.get("file") not in existing_files:
                    placeholders_found.append(ai_placeholder)

        except Exception as e:
            ai_analysis_result = {"error": str(e), "note": "AI analysis failed, using pattern-based detection only"}

    passed = len(placeholders_found) == 0
    if passed:
        reason = "No placeholder code detected"
        if ai_analysis_result and not ai_analysis_result.get("error"):
            reason += f" (AI analyzed {ai_analysis_result.get('files_analyzed', 0)} files)"
    else:
        reason = f"Found {len(placeholders_found)} placeholder/stub issues"

    return {
        "passed": passed,
        "placeholders_found": placeholders_found,
        "reason": reason,
        "ai_analysis": ai_analysis_result,
        "timestamp": datetime.utcnow().isoformat()
    }


def run_infrastructure_verification(project_dir: Path) -> dict:
    """
    Run terraform plan to verify infrastructure is actually deployed.

    THIS IS THE LAW:
    - Exit code 0 = no changes needed = infrastructure is deployed
    - Exit code 1 = error
    - Exit code 2 = changes needed = infrastructure NOT fully deployed

    The agent can claim terraform apply succeeded, but this verification
    will check if the state matches the configuration.

    Returns:
        dict with 'passed', 'exit_code', 'reason', 'timestamp'
    """
    infra_dir = project_dir / "infra/environments/dev"

    if not infra_dir.exists():
        return {
            "passed": False,
            "reason": f"Infrastructure directory not found: {infra_dir}",
            "exit_code": None,
            "timestamp": datetime.utcnow().isoformat()
        }

    # Check if terraform is initialized
    tf_dir = infra_dir / ".terraform"
    if not tf_dir.exists():
        return {
            "passed": False,
            "reason": "Terraform not initialized (no .terraform directory)",
            "exit_code": None,
            "timestamp": datetime.utcnow().isoformat()
        }

    try:
        # Get AWS credentials from environment or .env file
        env = _get_aws_env(project_dir)

        result = subprocess.run(
            ["terraform", "plan", "-detailed-exitcode", "-no-color"],
            cwd=infra_dir,
            capture_output=True,
            text=True,
            timeout=300,
            env=env
        )

        # Exit code 0 = no changes (success - infrastructure matches config)
        # Exit code 1 = error
        # Exit code 2 = changes needed (infrastructure not deployed or drifted)
        passed = result.returncode == 0

        if result.returncode == 0:
            reason = "No changes needed - infrastructure matches configuration"
        elif result.returncode == 1:
            reason = f"Terraform error: {result.stderr[:500]}"
        elif result.returncode == 2:
            # Count resources that need to be created/changed
            lines = result.stdout.split('\n')
            plan_line = [l for l in lines if 'Plan:' in l]
            if plan_line:
                reason = f"Changes needed: {plan_line[0]}"
            else:
                reason = "Changes needed - infrastructure not fully deployed"
        else:
            reason = f"Unexpected exit code: {result.returncode}"

        return {
            "passed": passed,
            "exit_code": result.returncode,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "output_tail": result.stdout[-2000:] if result.stdout else result.stderr[-2000:]
        }

    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "reason": "Terraform plan timed out after 300 seconds",
            "exit_code": None,
            "timestamp": datetime.utcnow().isoformat()
        }
    except FileNotFoundError:
        return {
            "passed": False,
            "reason": "Terraform command not found",
            "exit_code": None,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "passed": False,
            "reason": f"Error running terraform plan: {e}",
            "exit_code": None,
            "timestamp": datetime.utcnow().isoformat()
        }


def run_deployment_verification(project_dir: Path) -> dict:
    """
    Verify agent is deployed and responding.

    THIS IS THE LAW:
    1. agentcore status must show READY
    2. agentcore invoke must return a valid response

    The agent can claim deployment succeeded, but this verification
    will actually check if the agent is running and responding.

    Returns:
        dict with 'passed', 'reason', 'timestamp'
    """
    try:
        # Get AWS credentials from environment or .env file
        env = _get_aws_env(project_dir)

        # Check agentcore status
        status_result = subprocess.run(
            ["agentcore", "status"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )

        if status_result.returncode != 0:
            return {
                "passed": False,
                "reason": f"agentcore status failed: {status_result.stderr[:500]}",
                "timestamp": datetime.utcnow().isoformat()
            }

        if "READY" not in status_result.stdout:
            return {
                "passed": False,
                "reason": "Agent not in READY state",
                "status_output": status_result.stdout[:1000],
                "timestamp": datetime.utcnow().isoformat()
            }

        # Smoke test - invoke the agent with a simple prompt
        invoke_result = subprocess.run(
            ["agentcore", "invoke", '{"prompt": "Hello, are you working?"}'],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120,
            env=env
        )

        if invoke_result.returncode != 0:
            return {
                "passed": False,
                "reason": f"Agent invoke failed: {invoke_result.stderr[:500]}",
                "timestamp": datetime.utcnow().isoformat()
            }

        return {
            "passed": True,
            "reason": "Agent is READY and responding to invocations",
            "timestamp": datetime.utcnow().isoformat()
        }

    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "reason": "Agent verification timed out",
            "timestamp": datetime.utcnow().isoformat()
        }
    except FileNotFoundError:
        return {
            "passed": False,
            "reason": "agentcore command not found",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "passed": False,
            "reason": f"Error during deployment verification: {e}",
            "timestamp": datetime.utcnow().isoformat()
        }


def run_evaluation_verification(project_dir: Path) -> dict:
    """
    Verify evaluation scores exist and meet thresholds.

    THIS IS THE LAW:
    - Evaluation evidence file must exist at .evidence/evaluation_results.json
    - All required metrics must have actual scores
    - All scores must meet their thresholds

    The agent can claim evaluation passed, but this verification
    will check for actual evidence with real scores.

    Returns:
        dict with 'passed', 'reason', 'scores', 'timestamp'
    """
    evidence_file = project_dir / ".evidence/evaluation_results.json"

    if not evidence_file.exists():
        return {
            "passed": False,
            "reason": f"Evaluation evidence file not found: {evidence_file}",
            "required_file": str(evidence_file),
            "timestamp": datetime.utcnow().isoformat()
        }

    try:
        with open(evidence_file) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {
            "passed": False,
            "reason": f"Invalid JSON in evaluation evidence: {e}",
            "timestamp": datetime.utcnow().isoformat()
        }

    # Verify all required metrics exist and meet thresholds
    missing_metrics = []
    failed_metrics = []
    passing_metrics = []

    # Handle both formats:
    # 1. Top-level metrics: data["helpfulness"]["actual"]
    # 2. Nested results: data["results"]["helpfulness"]["score"]
    metrics_data = data.get("results", data)

    for metric, threshold in REQUIRED_EVALUATION_METRICS.items():
        if metric not in metrics_data:
            missing_metrics.append(metric)
            continue

        metric_data = metrics_data[metric]

        # Handle both "actual" and "score" keys
        actual = metric_data.get("actual") or metric_data.get("score")

        if actual is None:
            missing_metrics.append(f"{metric} (no actual/score value)")
            continue

        if actual < threshold:
            failed_metrics.append(f"{metric}: {actual:.2%} < {threshold:.0%}")
        else:
            passing_metrics.append(f"{metric}: {actual:.2%} >= {threshold:.0%}")

    if missing_metrics or failed_metrics:
        reasons = []
        if missing_metrics:
            reasons.append(f"Missing: {', '.join(missing_metrics)}")
        if failed_metrics:
            reasons.append(f"Below threshold: {', '.join(failed_metrics)}")

        return {
            "passed": False,
            "reason": "; ".join(reasons),
            "missing_metrics": missing_metrics,
            "failed_metrics": failed_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }

    return {
        "passed": True,
        "reason": "All evaluation thresholds met",
        "scores": data,
        "passing_metrics": passing_metrics,
        "timestamp": datetime.utcnow().isoformat()
    }


def update_features_based_on_verification(
    project_dir: Path,
    infra_result: dict,
    deploy_result: dict,
    eval_result: dict,
    placeholder_result: dict = None
) -> dict:
    """
    Update feature_list.json based on harness verification results.

    THIS IS THE LAW:
    - Only the harness can mark deployment/infrastructure/evaluation features complete
    - The agent's claims are overwritten based on verification results
    - If verification fails, features are marked as NOT passing
    - If placeholder code is detected, related features are marked as NOT passing

    Args:
        project_dir: Path to project directory
        infra_result: Result from infrastructure verification
        deploy_result: Result from deployment verification
        eval_result: Result from evaluation verification
        placeholder_result: Result from placeholder detection (optional)

    Returns:
        dict with counts of updated features by category
    """
    feature_list_path = project_dir / "feature_list.json"

    if not feature_list_path.exists():
        return {"error": "feature_list.json not found"}

    with open(feature_list_path) as f:
        data = json.load(f)

    updates = {"infrastructure": 0, "deployment": 0, "evaluation": 0, "placeholder_blocked": 0, "unchanged": 0}

    # Build list of features blocked by placeholder detection with REASONS
    placeholder_blocked_features = {}  # title -> reason
    if placeholder_result and not placeholder_result.get("passed", True):
        for issue in placeholder_result.get("placeholders_found", []):
            issue_file = issue.get("file", "unknown")
            issue_desc = issue.get("issue", "placeholder detected")

            # Block features related to lambdas if lambda placeholders found
            if issue.get("type") in ["lambda_placeholder", "missing_implementation"]:
                reason = f"Placeholder: {issue_file} - {issue_desc}"
                placeholder_blocked_features["Lambda functions exist"] = reason
                placeholder_blocked_features["Lambda extractor module"] = reason
                placeholder_blocked_features["Lambda processor module"] = reason
                placeholder_blocked_features["EventBridge schedule"] = reason
                placeholder_blocked_features["S3 event notification"] = reason

            # Block features related to data pipeline if buckets empty
            if issue.get("type") == "empty_bucket":
                reason = f"Empty bucket: {issue_file} - {issue_desc}"
                placeholder_blocked_features["S3 Vectors index exists"] = reason
                placeholder_blocked_features["Bedrock KB exists"] = reason

            # Block features related to source code placeholders
            if issue.get("type") == "python_placeholder":
                reason = f"Placeholder code in {issue_file} - {issue_desc}"
                # Try to identify which feature(s) this affects
                if "slack" in issue_file.lower():
                    placeholder_blocked_features["Slack message handling"] = reason
                    placeholder_blocked_features["Slack integration"] = reason

    for feature in data.get("features", []):
        category = feature.get("category", "")
        title = feature.get("title", "")
        dod = feature.get("dod_checklist", {})

        # Check if feature is blocked by placeholder detection
        if title in placeholder_blocked_features:
            dod["code_complete"] = False
            feature["passes"] = False
            feature["blocked_by"] = "placeholder_detection"
            feature["block_reason"] = placeholder_blocked_features[title]
            updates["placeholder_blocked"] += 1
            feature["dod_checklist"] = dod
            continue

        # Infrastructure features - controlled by terraform verification
        if category == "infrastructure":
            if infra_result["passed"]:
                dod["deployed"] = True
                dod["smoke_tests_pass"] = True
                dod["integration_tests_pass"] = True
                # Feature passes only if code is also complete
                feature["passes"] = all([
                    dod.get("code_complete", False),
                    dod.get("unit_tests_pass", False),
                ])
                if feature["passes"]:
                    updates["infrastructure"] += 1
                    # Clear any previous block
                    feature.pop("blocked_by", None)
                    feature.pop("block_reason", None)
            else:
                # Verification failed - mark as NOT deployed
                dod["deployed"] = False
                dod["smoke_tests_pass"] = False
                dod["integration_tests_pass"] = False
                feature["passes"] = False
                feature["blocked_by"] = "infrastructure_verification"
                feature["block_reason"] = f"Terraform: {infra_result.get('reason', 'verification failed')}"

        # Deployment features - controlled by agentcore verification
        elif category == "deployment":
            if deploy_result["passed"]:
                dod["deployed"] = True
                dod["smoke_tests_pass"] = True
                dod["integration_tests_pass"] = True
                feature["passes"] = True
                updates["deployment"] += 1
                # Clear any previous block
                feature.pop("blocked_by", None)
                feature.pop("block_reason", None)
            else:
                dod["deployed"] = False
                dod["smoke_tests_pass"] = False
                feature["passes"] = False
                feature["blocked_by"] = "deployment_verification"
                feature["block_reason"] = f"AgentCore: {deploy_result.get('reason', 'agent not READY')}"

        # Evaluation features - controlled by evaluation verification
        elif category == "evaluation":
            if eval_result["passed"]:
                dod["evaluation_threshold_met"] = True
                feature["passes"] = True
                # Store actual scores if available
                if "scores" in eval_result:
                    feature["evaluation_scores"] = eval_result["scores"]
                updates["evaluation"] += 1
                # Clear any previous block
                feature.pop("blocked_by", None)
                feature.pop("block_reason", None)
            else:
                dod["evaluation_threshold_met"] = False
                feature["passes"] = False
                feature["blocked_by"] = "evaluation_verification"
                feature["block_reason"] = f"Evaluation: {eval_result.get('reason', 'thresholds not met')}"

        else:
            updates["unchanged"] += 1

        feature["dod_checklist"] = dod

    # Save updated feature list
    with open(feature_list_path, "w") as f:
        json.dump(data, f, indent=2)

    return updates


def run_post_session_verification(project_dir: Path, verbose: bool = True) -> dict:
    """
    Main entry point - run all verifications after agent session.

    THIS IS THE LAW - This function is called by the harness, not the agent.
    The agent cannot bypass this verification.

    Args:
        project_dir: Path to the project directory
        verbose: Whether to print progress messages

    Returns:
        dict with verification results and update counts
    """
    results = {}

    if verbose:
        print("\n" + "=" * 70)
        print("  POST-SESSION VERIFICATION (Harness-Controlled)")
        print("  THIS IS THE LAW - Agent claims are verified here")
        print("=" * 70)

    # 1. Placeholder detection (NEW - runs first)
    if verbose:
        print("\n[1/4] Detecting placeholder/stub code...")
    results["placeholder_detection"] = run_placeholder_detection(project_dir)
    if verbose:
        status = "PASS" if results["placeholder_detection"]["passed"] else "FAIL"
        print(f"      Result: {status}")
        print(f"      Reason: {results['placeholder_detection']['reason']}")
        if not results["placeholder_detection"]["passed"]:
            for issue in results["placeholder_detection"]["placeholders_found"][:5]:
                print(f"      - {issue['file']}: {issue['issue']}")
            if len(results["placeholder_detection"]["placeholders_found"]) > 5:
                print(f"      ... and {len(results['placeholder_detection']['placeholders_found']) - 5} more issues")

    # 2. Infrastructure verification
    if verbose:
        print("\n[2/4] Verifying infrastructure (terraform plan -detailed-exitcode)...")
    results["infrastructure"] = run_infrastructure_verification(project_dir)
    if verbose:
        status = "PASS" if results["infrastructure"]["passed"] else "FAIL"
        print(f"      Result: {status}")
        print(f"      Reason: {results['infrastructure']['reason']}")

    # 3. Deployment verification
    if verbose:
        print("\n[3/4] Verifying deployment (agentcore status + invoke)...")
    results["deployment"] = run_deployment_verification(project_dir)
    if verbose:
        status = "PASS" if results["deployment"]["passed"] else "FAIL"
        print(f"      Result: {status}")
        print(f"      Reason: {results['deployment']['reason']}")

    # 4. Evaluation verification
    if verbose:
        print("\n[4/4] Verifying evaluation (parsing evidence file)...")
    results["evaluation"] = run_evaluation_verification(project_dir)
    if verbose:
        status = "PASS" if results["evaluation"]["passed"] else "FAIL"
        print(f"      Result: {status}")
        print(f"      Reason: {results['evaluation']['reason']}")

    # 5. Update features based on verification
    if verbose:
        print("\n[5/5] Updating feature_list.json based on verification results...")
    updates = update_features_based_on_verification(
        project_dir,
        results["infrastructure"],
        results["deployment"],
        results["evaluation"],
        results["placeholder_detection"]
    )
    if verbose:
        print(f"      Placeholder-blocked features: {updates.get('placeholder_blocked', 0)}")
        print(f"      Infrastructure features updated: {updates.get('infrastructure', 0)}")
        print(f"      Deployment features updated: {updates.get('deployment', 0)}")
        print(f"      Evaluation features updated: {updates.get('evaluation', 0)}")

    results["updates"] = updates

    # 6. Write verification report
    report_path = project_dir / ".verification_report.json"
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "results": results,
        "summary": {
            "placeholder_detection_passed": results["placeholder_detection"]["passed"],
            "infrastructure_passed": results["infrastructure"]["passed"],
            "deployment_passed": results["deployment"]["passed"],
            "evaluation_passed": results["evaluation"]["passed"],
            "all_passed": all([
                results["placeholder_detection"]["passed"],
                results["infrastructure"]["passed"],
                results["deployment"]["passed"],
                results["evaluation"]["passed"]
            ])
        }
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    if verbose:
        print("\n" + "-" * 70)
        all_passed = report["summary"]["all_passed"]
        if all_passed:
            print("  ALL VERIFICATIONS PASSED")
        else:
            print("  SOME VERIFICATIONS FAILED - Features marked accordingly")
        print("-" * 70)

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python post_session_validator.py <project_dir>")
        sys.exit(1)

    project_dir = Path(sys.argv[1])
    if not project_dir.exists():
        print(f"Error: Project directory not found: {project_dir}")
        sys.exit(1)

    results = run_post_session_verification(project_dir)

    # Exit with appropriate code
    all_passed = all([
        results["placeholder_detection"]["passed"],
        results["infrastructure"]["passed"],
        results["deployment"]["passed"],
        results["evaluation"]["passed"]
    ])
    sys.exit(0 if all_passed else 1)
