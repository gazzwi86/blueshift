"""
Base Evaluator

Abstract base class for all evaluators. Evaluators score specific aspects
of agent responses (intent classification, tool selection, response quality, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class EvaluationScore:
    """Score from an evaluator."""
    metric_name: str
    score: float  # 0.0 to 1.0
    explanation: Optional[str] = None
    details: dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    @property
    def passed(self) -> bool:
        """Check if score passes default threshold (0.7)."""
        return self.score >= 0.7

    def passes_threshold(self, threshold: float) -> bool:
        """Check if score passes a specific threshold."""
        return self.score >= threshold


class BaseEvaluator(ABC):
    """
    Abstract base class for evaluators.

    Each evaluator is responsible for scoring one aspect of agent behavior.
    """

    def __init__(self, metric_name: str):
        self.metric_name = metric_name

    @abstractmethod
    def evaluate(
        self,
        query: str,
        response: str,
        expected: dict,
        context: dict = None
    ) -> EvaluationScore:
        """
        Evaluate the agent response.

        Args:
            query: The input query to the agent
            response: The agent's response
            expected: Expected behavior/output
            context: Additional context

        Returns:
            EvaluationScore with score and explanation
        """
        pass


class LLMJudgeEvaluator(BaseEvaluator):
    """
    Evaluator that uses an LLM as judge.

    Uses a smaller/faster model to evaluate responses against criteria.
    """

    def __init__(
        self,
        metric_name: str,
        criteria: str,
        model: str = "claude-3-haiku-20240307"
    ):
        super().__init__(metric_name)
        self.criteria = criteria
        self.model = model

    def evaluate(
        self,
        query: str,
        response: str,
        expected: dict,
        context: dict = None
    ) -> EvaluationScore:
        """Evaluate using LLM as judge."""
        # Build the judge prompt
        prompt = self._build_judge_prompt(query, response, expected)

        # Call the LLM (this would use the SDK in practice)
        # For now, return a placeholder
        try:
            score, explanation = self._call_llm_judge(prompt)
            return EvaluationScore(
                metric_name=self.metric_name,
                score=score,
                explanation=explanation
            )
        except Exception as e:
            return EvaluationScore(
                metric_name=self.metric_name,
                score=0.0,
                explanation=f"Evaluation failed: {str(e)}"
            )

    def _build_judge_prompt(
        self,
        query: str,
        response: str,
        expected: dict
    ) -> str:
        """Build the prompt for the LLM judge."""
        return f"""You are evaluating an AI agent's response.

EVALUATION CRITERIA:
{self.criteria}

USER QUERY:
{query}

AGENT RESPONSE:
{response}

EXPECTED BEHAVIOR:
{expected}

Score the response from 0.0 to 1.0 based on how well it meets the criteria.
Respond with ONLY a JSON object:
{{"score": 0.X, "explanation": "brief explanation"}}
"""

    def _call_llm_judge(self, prompt: str) -> tuple[float, str]:
        """
        Call the LLM to get a judgment.

        In real usage, this would call the Claude API.
        For now, returns a placeholder.
        """
        # This would be implemented with actual API call
        # Example:
        # from anthropic import Anthropic
        # client = Anthropic()
        # response = client.messages.create(...)
        # return parse_response(response)

        # Placeholder - in real implementation, this calls the API
        return 0.7, "Placeholder evaluation - implement with real API call"


class DeterministicEvaluator(BaseEvaluator):
    """
    Evaluator for deterministic checks that don't require LLM.

    Examples: tool selection, response format, keyword presence.
    """

    def __init__(self, metric_name: str, check_fn: callable):
        """
        Args:
            metric_name: Name of the metric
            check_fn: Function(query, response, expected) -> float
        """
        super().__init__(metric_name)
        self.check_fn = check_fn

    def evaluate(
        self,
        query: str,
        response: str,
        expected: dict,
        context: dict = None
    ) -> EvaluationScore:
        """Run the deterministic check."""
        try:
            score = self.check_fn(query, response, expected)
            return EvaluationScore(
                metric_name=self.metric_name,
                score=score,
                explanation=f"Deterministic check returned {score:.2f}"
            )
        except Exception as e:
            return EvaluationScore(
                metric_name=self.metric_name,
                score=0.0,
                explanation=f"Check failed: {str(e)}"
            )
