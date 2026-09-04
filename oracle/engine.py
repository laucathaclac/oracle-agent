"""ORACLE core investigation engine implementing the autonomous loop."""

import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from oracle.types import (
    InvestigationState,
    Observation,
    Hypothesis,
    Verdict,
    EvidenceSource,
    ConfidenceLevel,
)
from oracle.evidence_store import EvidenceStore
from oracle.planner import InvestigationPlanner
from oracle.critic import AdversarialCritic


class OracleInvestigation:
    """
    Core investigation engine.
    Loop: GOAL → PLAN → ACTION → OBSERVE → UPDATE STATE → REPLAN → VERDICT
    """

    def __init__(self, question: str, max_steps: int = 10):
        self.id = str(uuid.uuid4())
        self.question = question
        self.state = InvestigationState.INITIALIZED
        self.created_at = datetime.utcnow()
        self.max_steps = max_steps

        # Core components
        self.evidence_store = EvidenceStore()
        self.planner = None
        self.critic = None
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.primary_hypothesis_id: Optional[str] = None

        # History
        self.steps_taken = 0
        self.observations_made: List[Observation] = []
        self.plan_history: List[Dict] = []

    def initialize_hypotheses(self, hypotheses: List[str]) -> None:
        """Initialize competing hypotheses."""
        for i, statement in enumerate(hypotheses):
            hyp_id = str(uuid.uuid4())
            self.hypotheses[hyp_id] = Hypothesis(
                id=hyp_id,
                statement=statement,
                created_at=datetime.utcnow(),
                is_primary=(i == 0),
            )
            if i == 0:
                self.primary_hypothesis_id = hyp_id

    def add_observation(
        self,
        source: EvidenceSource,
        raw_data,
        interpretation: str,
        confidence: ConfidenceLevel,
    ) -> Observation:
        """Add observation to investigation."""
        obs = Observation(
            source=source,
            timestamp=datetime.utcnow(),
            raw_data=raw_data,
            interpretation=interpretation,
            confidence=confidence,
        )
        self.evidence_store.add_observation(obs)
        self.observations_made.append(obs)
        return obs

    def link_observation_to_hypothesis(
        self,
        observation: Observation,
        hypothesis_id: str,
        supporting: bool = True,
        strength: float = 0.5,
    ) -> None:
        """Link observation to hypothesis as evidence."""
        evidence = self.evidence_store.evaluate_observation(
            observation,
            supports=[hypothesis_id] if supporting else [],
            contradicts=[] if supporting else [hypothesis_id],
            supporting_strength=strength if supporting else 0.0,
            contradicting_strength=0.0 if supporting else strength,
            analysis="",
        )

        # Update hypothesis
        if hypothesis_id in self.hypotheses:
            hyp = self.hypotheses[hypothesis_id]
            if supporting:
                if evidence not in hyp.supporting_evidence:
                    hyp.supporting_evidence.append(evidence)
            else:
                if evidence not in hyp.contradicting_evidence:
                    hyp.contradicting_evidence.append(evidence)
            hyp.confidence_score = hyp.calculate_confidence()

    def run(self) -> Verdict:
        """Execute the investigation loop."""
        if not self.hypotheses:
            raise ValueError("No hypotheses initialized. Call initialize_hypotheses() first.")

        self.state = InvestigationState.PLANNING
        self.planner = InvestigationPlanner(self.id)
        self.critic = AdversarialCritic(self.evidence_store)

        # Main loop: GOAL → PLAN → ACTION → OBSERVE → UPDATE → REPLAN → VERDICT
        while self.steps_taken < self.max_steps:
            self.state = InvestigationState.PLANNING

            # PLAN: Decide next action
            plan_decision = self._plan_next_action()
            self.plan_history.append(plan_decision)

            # Check termination criteria
            if self._should_terminate():
                break

            # ACTION: Apply planner decision (in production, would execute tools)
            self.state = InvestigationState.EXECUTING

            # OBSERVE: Process any new observations (in production, from tools)
            self.state = InvestigationState.ANALYZING

            # UPDATE STATE: Recalculate all hypothesis confidence scores
            self._update_hypothesis_states()

            # CHALLENGE: Critic reviews the leading hypothesis
            self._apply_critic()

            # REPLAN: Adjust strategy
            self.steps_taken += 1

        # VERDICT: Generate final conclusion
        self.state = InvestigationState.CONCLUDING
        verdict = self._generate_verdict()
        self.state = InvestigationState.COMPLETED

        return verdict

    def _plan_next_action(self) -> Dict:
        """PLAN phase: Decide next investigation action."""
        primary = self._get_primary_hypothesis()
        evidence_count = self.evidence_store.summary()["total_evidence"]

        # Simple dynamic planning logic
        if evidence_count < 2:
            action = "gather_initial_evidence"
        elif primary.confidence_score < 0.5:
            action = "test_alternative_hypotheses"
        elif len(primary.contradicting_evidence) > 0:
            action = "investigate_contradictions"
        else:
            action = "validate_hypothesis"

        decision = {
            "step": self.steps_taken,
            "action": action,
            "timestamp": datetime.utcnow(),
            "rationale": f"Primary hypothesis confidence: {primary.confidence_score:.2f}",
        }

        return decision

    def _should_terminate(self) -> bool:
        """Determine if investigation should stop."""
        primary = self._get_primary_hypothesis()

        # Stop if high confidence and no critical contradictions
        if (
            primary.confidence_score > 0.75
            and len(primary.contradicting_evidence) == 0
        ):
            return True

        # Stop if sufficient evidence gathered
        if (
            self.evidence_store.summary()["total_evidence"] >= 5
            and primary.confidence_score > 0.6
        ):
            return True

        return False

    def _update_hypothesis_states(self) -> None:
        """UPDATE STATE: Recalculate confidence for all hypotheses."""
        for hyp_id, hyp in self.hypotheses.items():
            supporting, contradicting = self.evidence_store.get_evidence_for_hypothesis(
                hyp_id
            )
            hyp.supporting_evidence = supporting
            hyp.contradicting_evidence = contradicting
            hyp.confidence_score = hyp.calculate_confidence()

    def _apply_critic(self) -> None:
        """CHALLENGE: Apply adversarial critic."""
        primary = self._get_primary_hypothesis()
        challenges = self.critic.challenge_hypothesis(primary)

    def _get_primary_hypothesis(self) -> Hypothesis:
        """Get the primary (highest confidence) hypothesis."""
        if self.primary_hypothesis_id and self.primary_hypothesis_id in self.hypotheses:
            return self.hypotheses[self.primary_hypothesis_id]

        # Return highest confidence
        sorted_hyps = sorted(
            self.hypotheses.values(), key=lambda h: h.confidence_score, reverse=True
        )
        return sorted_hyps[0] if sorted_hyps else None

    def _generate_verdict(self) -> Verdict:
        """VERDICT: Generate final investigation conclusion."""
        primary = self._get_primary_hypothesis()
        all_evidence = self.evidence_store.get_all_evidence()

        supporting = (
            [e for e in all_evidence if primary.id in e.supports_hypotheses]
            if primary
            else []
        )
        contradicting = (
            [e for e in all_evidence if primary.id in e.contradicts_hypotheses]
            if primary
            else []
        )

        return Verdict(
            investigation_id=self.id,
            primary_hypothesis=primary,
            confidence=primary.confidence_score if primary else 0.5,
            supporting_evidence_count=len(supporting),
            contradicting_evidence_count=len(contradicting),
            summary=f"Investigation into '{self.question}' completed in {self.steps_taken} steps.",
            key_findings=[
                f"Primary: {primary.statement}" if primary else "No conclusion",
                f"Confidence: {primary.confidence_score:.0%}" if primary else "N/A",
            ],
            assumptions=["Tool outputs are accurate", "No systematic bias"],
            what_would_change_mind=self._determine_mind_change(primary),
            timestamp=datetime.utcnow(),
        )

    def _determine_mind_change(self, primary: Optional[Hypothesis]) -> str:
        """What evidence would overturn the conclusion?"""
        if not primary:
            return "Any hypothesis with evidence would change conclusion."
        if primary.confidence_score < 0.6:
            return "Strong evidence for an alternative hypothesis would change conclusion."
        return "Multiple independent sources contradicting primary hypothesis would be needed."

    def get_state(self) -> Dict:
        """Get current investigation state."""
        primary = self._get_primary_hypothesis()
        return {
            "id": self.id,
            "question": self.question,
            "state": self.state.value,
            "steps_taken": self.steps_taken,
            "primary_hypothesis": primary.statement if primary else None,
            "confidence": primary.confidence_score if primary else None,
            "evidence_count": self.evidence_store.summary()["total_evidence"],
            "hypotheses_count": len(self.hypotheses),
        }
