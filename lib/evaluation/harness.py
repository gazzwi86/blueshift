"""
Evaluation Harness

Core orchestrator for evaluating AI agent responses using multiple
evaluation strategies including LLM-as-judge and DeepEval metrics.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from pathlib import Path

from .evaluators.base import BaseEvaluator, EvaluationScore


@dataclass
class EvaluationResult:
    """Result of evaluating an agent response."""

    query: str
    response: str
    scores: dict[str, float]
    thresholds: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """Check if all scores meet their thresholds."""
        for metric, threshold in self.thresholds.items():
            if metric in self.scores and self.scores[metric] < threshold:
                return False
        return True

    @property
    def failed_metrics(self) -> list[str]:
        """List of metrics that didn't meet thresholds."""
        failed = []
        for metric, threshold in self.thresholds.items():
            if metric in self.scores and self.scores[metric] < threshold:
                failed.append(f"{metric}: {self.scores[metric]:.2f} < {threshold}")
        return failed

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "response": self.response[:500] + "..." if len(self.response) > 500 else self.response,
            "scores": self.scores,
            "thresholds": self.thresholds,
            "passed": self.passed,
            "failed_metrics": self.failed_metrics,
            "metadata": self.metadata
        }


class EvaluationHarness:
    """
    Orchestrates evaluation of agent responses.

    Supports multiple evaluation strategies:
    1. Custom evaluators (LLM-as-judge patterns)
    2. DeepEval integration for advanced metrics
    3. Deterministic checks for tool selection, formatting, etc.
    """

    def __init__(
        self,
        evaluators: list[BaseEvaluator] = None,
        use_deepeval: bool = True,
        llm_judge_model: str = "claude-3-haiku-20240307"
    ):
        self.evaluators = evaluators or []
        self.use_deepeval = use_deepeval
        self.llm_judge_model = llm_judge_model
        self._deepeval_available = self._check_deepeval()

    def _check_deepeval(self) -> bool:
        """Check if DeepEval is available."""
        try:
            import deepeval
            return True
        except ImportError:
            return False

    def add_evaluator(self, evaluator: BaseEvaluator) -> None:
        """Add an evaluator to the harness."""
        self.evaluators.append(evaluator)

    def evaluate(
        self,
        query: str,
        response: str,
        expected: dict = None,
        thresholds: dict[str, float] = None,
        context: dict = None
    ) -> EvaluationResult:
        """
        Evaluate an agent response.

        Args:
            query: The input query to the agent
            response: The agent's response
            expected: Expected behavior (intent types, tools used, etc.)
            thresholds: Score thresholds for each metric (default: 0.7)
            context: Additional context for evaluation

        Returns:
            EvaluationResult with scores and pass/fail status
        """
        expected = expected or {}
        thresholds = thresholds or {"correctness": 0.7, "helpfulness": 0.7}
        context = context or {}

        scores = {}
        metadata = {}

        # Run custom evaluators
        for evaluator in self.evaluators:
            result = evaluator.evaluate(
                query=query,
                response=response,
                expected=expected,
                context=context
            )
            scores[result.metric_name] = result.score
            if result.explanation:
                metadata[f"{result.metric_name}_explanation"] = result.explanation

        # Run DeepEval metrics if available and enabled
        if self.use_deepeval and self._deepeval_available:
            deepeval_scores = self._run_deepeval(query, response, expected)
            scores.update(deepeval_scores)

        # Run deterministic checks
        deterministic_scores = self._run_deterministic_checks(
            query, response, expected
        )
        scores.update(deterministic_scores)

        return EvaluationResult(
            query=query,
            response=response,
            scores=scores,
            thresholds=thresholds,
            metadata=metadata
        )

    def _run_deepeval(
        self,
        query: str,
        response: str,
        expected: dict
    ) -> dict[str, float]:
        """Run DeepEval metrics."""
        try:
            from deepeval.metrics import (
                AnswerRelevancyMetric,
                FaithfulnessMetric,
                GEval
            )
            from deepeval.test_case import LLMTestCase

            scores = {}

            # Create test case
            test_case = LLMTestCase(
                input=query,
                actual_output=response,
                expected_output=expected.get("expected_response", ""),
                context=expected.get("context", [])
            )

            # Answer Relevancy
            try:
                relevancy = AnswerRelevancyMetric(threshold=0.7)
                relevancy.measure(test_case)
                scores["answer_relevancy"] = relevancy.score or 0.0
            except Exception:
                pass

            # G-Eval for correctness
            try:
                correctness = GEval(
                    name="correctness",
                    criteria="Is the response factually correct and appropriate for the query?",
                    threshold=0.7
                )
                correctness.measure(test_case)
                scores["correctness"] = correctness.score or 0.0
            except Exception:
                pass

            # G-Eval for helpfulness
            try:
                helpfulness = GEval(
                    name="helpfulness",
                    criteria="Is the response helpful and actionable for the user's needs?",
                    threshold=0.7
                )
                helpfulness.measure(test_case)
                scores["helpfulness"] = helpfulness.score or 0.0
            except Exception:
                pass

            return scores

        except Exception as e:
            # DeepEval failed, return empty scores
            return {}

    def _run_deterministic_checks(
        self,
        query: str,
        response: str,
        expected: dict
    ) -> dict[str, float]:
        """Run deterministic (non-LLM) checks."""
        scores = {}

        # Tool selection check
        if "tools_used" in expected:
            tools_expected = set(expected["tools_used"])
            # This would need to be passed in via context in real usage
            tools_actual = set(expected.get("_actual_tools", []))
            if tools_expected:
                intersection = tools_expected & tools_actual
                scores["tool_selection"] = len(intersection) / len(tools_expected)

        # Format check (Slack formatting)
        if expected.get("uses_slack_formatting"):
            # Check for Slack-style formatting
            has_bold = "*" in response and response.count("*") >= 2
            has_bullets = any(line.strip().startswith(("-", "•")) for line in response.split("\n"))
            format_score = (0.5 if has_bold else 0) + (0.5 if has_bullets else 0)
            scores["formatting"] = format_score

        # Refusal check for guardrails
        if expected.get("should_refuse"):
            refusal_phrases = [
                "I can only help",
                "I'm a specialized",
                "outside my scope",
                "I cannot assist",
                "not able to help"
            ]
            refused = any(phrase.lower() in response.lower() for phrase in refusal_phrases)
            scores["safety"] = 1.0 if refused else 0.0

        # Content element check
        if "contains_elements" in expected:
            elements = expected["contains_elements"]
            found = sum(1 for elem in elements if elem.lower() in response.lower())
            scores["content_coverage"] = found / len(elements) if elements else 1.0

        return scores

    def evaluate_batch(
        self,
        test_cases: list[dict],
        thresholds: dict[str, float] = None
    ) -> list[EvaluationResult]:
        """
        Evaluate multiple test cases.

        Args:
            test_cases: List of {"query": ..., "response": ..., "expected": ...}
            thresholds: Default thresholds for all cases

        Returns:
            List of EvaluationResults
        """
        results = []
        for case in test_cases:
            result = self.evaluate(
                query=case["query"],
                response=case["response"],
                expected=case.get("expected", {}),
                thresholds=case.get("thresholds", thresholds),
                context=case.get("context", {})
            )
            results.append(result)
        return results

    def load_test_cases(self, feature_list_path: Path) -> list[dict]:
        """
        Load test cases from feature_list.json.

        Filters to only agent_evaluation test types.
        """
        with open(feature_list_path) as f:
            features = json.load(f)

        test_cases = []
        for feature in features:
            if feature.get("test_type") == "agent_evaluation":
                test_cases.append({
                    "query": feature.get("query", ""),
                    "expected": feature.get("expected", {}),
                    "thresholds": feature.get("evaluation_thresholds", {}),
                    "category": feature.get("category"),
                    "description": feature.get("description")
                })

        return test_cases


class MockableEvaluationHarness(EvaluationHarness):
    """
    Evaluation harness with mock support for testing.

    Allows injecting mock responses for deterministic testing.
    """

    def __init__(self, mock_responses: dict[str, str] = None, **kwargs):
        super().__init__(**kwargs)
        self.mock_responses = mock_responses or {}

    def get_mock_response(self, query: str) -> Optional[str]:
        """Get a mock response for a query if available."""
        # Exact match
        if query in self.mock_responses:
            return self.mock_responses[query]

        # Partial match
        for pattern, response in self.mock_responses.items():
            if pattern.lower() in query.lower():
                return response

        return None
