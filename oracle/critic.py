"""Adversarial critic for challenging hypotheses."""

from typing import List
from datetime import datetime
from oracle.types import Hypothesis, Observation, Evidence, EvidenceSource, ConfidenceLevel
from oracle.evidence_store import EvidenceStore


class AdversarialCritic:
    """Actively searches for evidence that contradicts the leading hypothesis."""

    def __init__(self, evidence_store: EvidenceStore):
        self.evidence_store = evidence_store
        self.critique_history: List[str] = []

    def challenge_hypothesis(self, hypothesis: Hypothesis) -> List[str]:
        """Generate challenges to the hypothesis."""
        challenges = []

        # Challenge 1: Evidence distribution
        if len(hypothesis.supporting_evidence) == 0:
            challenges.append(
                f"Hypothesis '{hypothesis.statement}' has NO supporting evidence. "
                "This is an unfounded claim."
            )

        # Challenge 2: Contradicting evidence strength
        if hypothesis.contradicting_evidence:
            contradict_strength = sum(
                e.contradicting_strength for e in hypothesis.contradicting_evidence
            )
            support_strength = sum(
                e.supporting_strength for e in hypothesis.supporting_evidence
            )
            if contradict_strength > support_strength:
                challenges.append(
                    f"Hypothesis '{hypothesis.statement}' is contradicted by strong evidence. "
                    f"Contradicting strength: {contradict_strength:.2f} vs Supporting: {support_strength:.2f}"
                )

        # Challenge 3: Confidence overstatement
        if hypothesis.confidence_score > 0.8 and len(hypothesis.supporting_evidence) < 3:
            challenges.append(
                f"Hypothesis '{hypothesis.statement}' has high confidence ({hypothesis.confidence_score:.2f}) "
                f"but only {len(hypothesis.supporting_evidence)} supporting evidence items. "
                "Insufficient evidence for such high confidence."
            )

        # Challenge 4: Missing alternative explanations
        challenges.append(
            f"Alternative hypotheses should be considered. The hypothesis '{hypothesis.statement}' "
            "may be subject to confirmation bias."
        )

        self.critique_history.extend(challenges)
        return challenges

    def identify_evidence_gaps(
        self, hypothesis: Hypothesis, all_hypotheses: List[Hypothesis]
    ) -> List[str]:
        """Identify what evidence would be needed to falsify or support the hypothesis."""
        gaps = []

        # Identify unexplored evidence sources
        evidence_sources = set(e.observation.source for e in hypothesis.supporting_evidence)
        if EvidenceSource.ON_CHAIN not in evidence_sources:
            gaps.append(
                "Missing on-chain analysis. Need: blockchain transaction volumes, holder distribution, "
                "smart contract interactions."
            )
        if EvidenceSource.SOCIAL_SENTIMENT not in evidence_sources:
            gaps.append(
                "Missing social sentiment data. Need: community discussion trends, influence metrics, "
                "sentiment polarity."
            )
        if EvidenceSource.NEWS not in evidence_sources:
            gaps.append(
                "Missing news/event analysis. Need: regulatory announcements, partnership news, "
                "technical developments."
            )

        # What would disprove this hypothesis?
        if hypothesis.statement.lower().find("bullish") > -1:
            gaps.append(
                "FALSIFICATION: Sharp market reversal or negative regulatory action would contradict "
                "this bullish hypothesis."
            )
        elif hypothesis.statement.lower().find("bearish") > -1:
            gaps.append(
                "FALSIFICATION: Unexpected positive catalyst or sustained recovery would contradict "
                "this bearish hypothesis."
            )

        return gaps

    def propose_disproving_tests(
        self, hypothesis: Hypothesis
    ) -> List[Dict[str, str]]:
        """Propose tests that could disprove the hypothesis."""
        tests = []

        tests.append(
            {
                "test": "Check for contradicting recent news",
                "method": "Scan crypto news for announcements that contradict the hypothesis",
                "expected_outcome": "Find evidence that would refute the hypothesis",
            }
        )

        tests.append(
            {
                "test": "Validate assumption consistency",
                "method": "Verify if underlying assumptions in the hypothesis remain valid",
                "expected_outcome": "Detect if assumptions have been invalidated",
            }
        )

        tests.append(
            {
                "test": "Look for counterexamples",
                "method": "Search for similar past scenarios with opposite outcomes",
                "expected_outcome": "Find precedents that contradict the pattern",
            }
        )

        return tests

    def get_critique_summary(self) -> Dict[str, List[str]]:
        """Get summary of all critiques."""
        return {
            "total_critiques": len(self.critique_history),
            "critiques": self.critique_history[-10:],  # Last 10 critiques
        }
