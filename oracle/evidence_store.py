"""Evidence store for managing observations and their relationships to hypotheses."""

from typing import List, Dict, Set
from datetime import datetime
from oracle.types import Evidence, Observation, Hypothesis, EvidenceSource


class EvidenceStore:
    """Manages evidence collection, evaluation, and hypothesis scoring."""

    def __init__(self):
        self.evidence: List[Evidence] = []
        self.observations: List[Observation] = []
        self._evidence_by_source: Dict[EvidenceSource, List[Evidence]] = {}
        self._evidence_by_hypothesis: Dict[str, List[Evidence]] = {}

    def add_observation(self, observation: Observation) -> None:
        """Record a raw observation."""
        self.observations.append(observation)

    def evaluate_observation(
        self,
        observation: Observation,
        supports: List[str] = None,
        contradicts: List[str] = None,
        supporting_strength: float = 0.5,
        contradicting_strength: float = 0.0,
        analysis: str = "",
    ) -> Evidence:
        """Convert observation to evidence with hypothesis relationships."""
        supports = supports or []
        contradicts = contradicts or []

        evidence = Evidence(
            observation=observation,
            supports_hypotheses=supports,
            contradicts_hypotheses=contradicts,
            supporting_strength=supporting_strength,
            contradicting_strength=contradicting_strength,
            analysis=analysis,
        )

        self.evidence.append(evidence)

        # Index by source
        if observation.source not in self._evidence_by_source:
            self._evidence_by_source[observation.source] = []
        self._evidence_by_source[observation.source].append(evidence)

        # Index by hypothesis
        for hyp_id in supports + contradicts:
            if hyp_id not in self._evidence_by_hypothesis:
                self._evidence_by_hypothesis[hyp_id] = []
            self._evidence_by_hypothesis[hyp_id].append(evidence)

        return evidence

    def get_evidence_for_hypothesis(self, hypothesis_id: str) -> tuple[List[Evidence], List[Evidence]]:
        """Get supporting and contradicting evidence for a hypothesis."""
        all_evidence = self._evidence_by_hypothesis.get(hypothesis_id, [])
        supporting = [e for e in all_evidence if hypothesis_id in e.supports_hypotheses]
        contradicting = [e for e in all_evidence if hypothesis_id in e.contradicts_hypotheses]
        return supporting, contradicting

    def get_evidence_by_source(self, source: EvidenceSource) -> List[Evidence]:
        """Get all evidence from a specific source."""
        return self._evidence_by_source.get(source, [])

    def get_all_evidence(self) -> List[Evidence]:
        """Get all evidence."""
        return self.evidence.copy()

    def summary(self) -> Dict:
        """Get a summary of the evidence store."""
        return {
            "total_observations": len(self.observations),
            "total_evidence": len(self.evidence),
            "sources": {
                source.value: len(evidence)
                for source, evidence in self._evidence_by_source.items()
            },
            "hypotheses_with_evidence": len(self._evidence_by_hypothesis),
        }
