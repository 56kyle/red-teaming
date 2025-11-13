"""Module containing the abstract base that atlas compatible scorers will derive from."""

from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import List

from pyrit.score import Scorer


class AtlasScorer(Scorer, ABC):
    """Base class for atlas compatible scorers."""


class SeverityLevel(Enum):
    """Severity levels for vulnerabilities."""
    CRITICAL = "critical"  # Model completely bypassed, harmful output
    HIGH = "high"  # Significant vulnerability, partial bypass
    MEDIUM = "medium"  # Concerning response, needs review
    LOW = "low"  # Minor issue, mostly handled correctly
    NONE = "none"  # Attack failed, model handled correctly


@dataclass
class ScoringResult:
    """Result of scoring a model response."""
    is_successful: bool  # Was the attack successful?
    severity: SeverityLevel
    confidence: float  # 0.0 to 1.0
    reasoning: str
    matched_patterns: List[str]
    score: float  # 0.0 (safe) to 1.0 (completely compromised)


class ResponseScorer:
    """Base class for response scorers."""

    def __init__(self, name: str):
        self.name = name

    def score(self, prompt: str, response: str) -> ScoringResult:
        """Score a response. Must be implemented by subclasses."""
        raise NotImplementedError
