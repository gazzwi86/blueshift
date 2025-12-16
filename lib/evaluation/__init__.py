"""
Agent Evaluation Framework

Provides LLM-as-judge evaluation for AI agent responses, with optional
DeepEval integration for advanced metrics.

Usage:
    from lib.evaluation import EvaluationHarness, EvaluationResult

    harness = EvaluationHarness()
    result = harness.evaluate(
        query="Find AWS certified architects",
        response=agent_response,
        expected={"intent_types": ["certification", "role"]},
        thresholds={"correctness": 0.7, "helpfulness": 0.7}
    )

    if result.passed:
        print("All thresholds met!")
    else:
        print(f"Failed metrics: {result.failed_metrics}")
"""

from .harness import EvaluationHarness, EvaluationResult
from .evaluators.base import BaseEvaluator

__all__ = [
    "EvaluationHarness",
    "EvaluationResult",
    "BaseEvaluator",
]
