"""Adversarial critic for challenging hypotheses."""

from typing import List, Dict
from oracle.types import Hypothesis, EvidenceSource
from oracle.evidence_store import EvidenceStore


class AdversarialCritic:
    """Actively searches for evidence that contradicts the leading hypothesis."""

    def __init__(self, evidence_store: EvidenceStore):
        self.evidence_store = evidence_store
        self.critique_history: List[str] = []

    def challenge_hypothesis(self, hypothesis: Hypothesis) -> List[str]:
        """Generate concise, auditable challenges to the hypothesis."""
        challenges = []

        if len(hypothesis.supporting_evidence) == 0:
            challenges.append(
                f"Hypothesis '{hypothesis.statement}' has NO supporting evidence. This is an unfounded claim."
            )

        if hypothesis.contradicting_evidence:
            contradict_strength = sum(e.contradicting_strength for e in hypothesis.contradicting_evidence)
            support_strength = sum(e.supporting_strength for e in hypothesis.supporting_evidence)
            if contradict_strength > support_strength:
                challenges.append(
                    f"Hypothesis '{hypothesis.statement}' is contradicted by strong evidence. "
                    f"Contradicting strength: {contradict_strength:.2f} vs Supporting: {support_strength:.2f}"
                )

        if hypothesis.confidence_score > 0.8 and len(hypothesis.supporting_evidence) < 3:
            challenges.append(
                f"Hypothesis '{hypothesis.statement}' has high confidence ({hypothesis.confidence_score:.2f}) "
                f"but only {len(hypothesis.supporting_evidence)} supporting evidence items."
            )

        challenges.append(
            f"Alternative hypotheses should be considered; '{hypothesis.statement}' may be subject to confirmation bias."
        )
        self.critique_history.extend(challenges)
        return challenges

    def identify_evidence_gaps(self, hypothesis: Hypothesis, all_hypotheses: List[Hypothesis]) -> List[str]:
        """Identify evidence needed to strengthen or falsify the hypothesis."""
        gaps = []
        evidence_sources = {e.observation.source for e in hypothesis.supporting_evidence}
        if EvidenceSource.ON_CHAIN not in evidence_sources:
            gaps.append("Missing on-chain analysis.")
        if EvidenceSource.SOCIAL_SENTIMENT not in evidence_sources:
            gaps.append("Missing social sentiment data.")
        if EvidenceSource.NEWS not in evidence_sources:
            gaps.append("Missing news/event analysis.")

        statement = hypothesis.statement.lower()
        if "bullish" in statement:
            gaps.append("FALSIFICATION: A sharp reversal or major negative catalyst would contradict this hypothesis.")
        elif "bearish" in statement:
            gaps.append("FALSIFICATION: A sustained recovery or strong positive catalyst would contradict this hypothesis.")
        return gaps

    def propose_disproving_tests(self, hypothesis: Hypothesis) -> List[Dict[str, str]]:
        """Propose concrete tests that could disprove the hypothesis."""
        return [
            {
                "test": "Check contradicting recent news",
                "method": "Scan current events for announcements that conflict with the hypothesis.",
                "expected_outcome": "Find evidence that could refute the hypothesis.",
            },
            {
                "test": "Validate assumption consistency",
                "method": "Verify whether the assumptions behind the hypothesis remain valid.",
                "expected_outcome": "Detect invalidated assumptions.",
            },
            {
                "test": "Look for counterexamples",
                "method": "Compare with similar historical market regimes.",
                "expected_outcome": "Find precedents with opposite outcomes.",
            },
        ]

    def get_critique_summary(self) -> Dict[str, object]:
        """Return a compact audit summary."""
        return {
            "total_critiques": len(self.critique_history),
            "critiques": self.critique_history[-10:],
        }
