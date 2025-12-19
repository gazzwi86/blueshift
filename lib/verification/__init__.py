"""
Verification Module
==================

THIS IS THE LAW - Harness-controlled verification that the agent cannot bypass.

This module runs AFTER each agent session to verify claims made by the agent.
The agent can claim whatever it wants in feature_list.json, but the harness
will verify those claims and update the features based on actual evidence.

Verification Checks:
1. Placeholder Detection: Pattern-based AND AI-powered detection of stub code
2. Infrastructure: terraform plan -detailed-exitcode (exit code 0 = no changes = deployed)
3. Deployment: agentcore status + invoke (READY + responds = deployed)
4. Evaluation: .evidence/evaluation_results.json exists with scores meeting thresholds

MOCKS ARE NOT SUFFICIENT. This runs real commands against real infrastructure.
AI-POWERED ANALYSIS provides robust detection of subtle placeholder patterns.
"""

from .post_session_validator import (
    run_post_session_verification,
    run_infrastructure_verification,
    run_deployment_verification,
    run_evaluation_verification,
    run_placeholder_detection,
    update_features_based_on_verification,
    REQUIRED_EVALUATION_METRICS,
)

# AI-powered code analysis (optional)
try:
    from .ai_code_analyzer import (
        detect_placeholders_with_ai,
        quick_placeholder_check,
        analyze_code_with_ai,
    )
    AI_ANALYZER_AVAILABLE = True
except ImportError:
    AI_ANALYZER_AVAILABLE = False
    detect_placeholders_with_ai = None
    quick_placeholder_check = None
    analyze_code_with_ai = None

__all__ = [
    "run_post_session_verification",
    "run_infrastructure_verification",
    "run_deployment_verification",
    "run_evaluation_verification",
    "run_placeholder_detection",
    "update_features_based_on_verification",
    "REQUIRED_EVALUATION_METRICS",
    "AI_ANALYZER_AVAILABLE",
    "detect_placeholders_with_ai",
    "quick_placeholder_check",
    "analyze_code_with_ai",
]
