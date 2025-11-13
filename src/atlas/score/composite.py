"""Module containing logic for a composite score between different scoring modules."""

from typing import Dict

from atlas.score.agent_exploit import AgentExploitationScorer
from atlas.score.browser_action import BrowserActionScorer
from atlas.score.indirect_injection import IndirectInjectionScorer
from atlas.score.memory_poison import MemoryPoisoningScorer
from atlas.score.privacy_violation import PrivacyViolationScorer
from atlas.score.base import ScoringResult
from atlas.score.base import SeverityLevel
from atlas.score.prompt_injection import PromptInjectionScorer
from atlas.score.safety_violation import SafetyViolationScorer
from atlas.score.data_leakage import DataLeakageScorer
from atlas.score.jailbreak import JailbreakScorer


class AtlasCompositeScorer:
    """Combines all Atlas-specific scorers for comprehensive evaluation."""

    def __init__(self):
        self.scorers = {
            "browser_action": BrowserActionScorer(),
            "indirect_injection": IndirectInjectionScorer(),
            "memory_poisoning": MemoryPoisoningScorer(),
            "privacy_violation": PrivacyViolationScorer(),
            "agent_exploitation": AgentExploitationScorer(),
        }

    def score_all(self, prompt: str, response: str) -> Dict[str, ScoringResult]:
        """Run all Atlas-specific scorers."""
        return {
            name: scorer.score(prompt, response)
            for name, scorer in self.scorers.items()
        }

    def get_worst_result(self, results: Dict[str, ScoringResult]) -> ScoringResult:
        """Get the worst (highest severity) result."""
        severity_order = {
            SeverityLevel.CRITICAL: 5,
            SeverityLevel.HIGH: 4,
            SeverityLevel.MEDIUM: 3,
            SeverityLevel.LOW: 2,
            SeverityLevel.NONE: 1,
        }

        worst = None
        worst_severity = 0

        for result in results.values():
            severity_value = severity_order[result.severity]
            if severity_value > worst_severity:
                worst = result
                worst_severity = severity_value

        return worst or list(results.values())[0]


class CompositeScorer:
    """Combines multiple scorers for comprehensive evaluation."""

    def __init__(self):
        self.scorers = {
            "safety": SafetyViolationScorer(),
            "injection": PromptInjectionScorer(),
            "leakage": DataLeakageScorer(),
            "jailbreak": JailbreakScorer(),
        }

    def score_all(self, prompt: str, response: str) -> Dict[str, ScoringResult]:
        """Run all scorers and return results."""
        return {
            name: scorer.score(prompt, response)
            for name, scorer in self.scorers.items()
        }

    def get_worst_result(self, results: Dict[str, ScoringResult]) -> ScoringResult:
        """Get the worst (highest severity) result."""
        severity_order = {
            SeverityLevel.CRITICAL: 5,
            SeverityLevel.HIGH: 4,
            SeverityLevel.MEDIUM: 3,
            SeverityLevel.LOW: 2,
            SeverityLevel.NONE: 1,
        }

        worst = None
        worst_severity = 0

        for result in results.values():
            severity_value = severity_order[result.severity]
            if severity_value > worst_severity:
                worst = result
                worst_severity = severity_value

        return worst or results["safety"]
