"""ORACLE autonomous investigation engine.

Coordinates planning, tool execution, evidence updates, adversarial critique,
persistence checkpoints, and confidence-rated verdict generation.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

from oracle.types import InvestigationState, Observation, Hypothesis, Verdict, EvidenceSource, ConfidenceLevel
from oracle.evidence_store import EvidenceStore
from oracle.planner import InvestigationPlanner
from oracle.critic import AdversarialCritic
from oracle.executor import ToolRegistry, ToolResult


class OracleInvestigation:
    """Core loop: GOAL → PLAN → ACTION → OBSERVE → UPDATE → CRITIQUE → REPLAN → VERDICT."""

    def __init__(self, question: str, max_steps: int = 10,
                 tool_registry: Optional[ToolRegistry] = None,
                 persistence: Optional[Any] = None):
        if not question or not question.strip():
            raise ValueError("question must not be empty")
        if max_steps < 1:
            raise ValueError("max_steps must be >= 1")
        self.id = str(uuid.uuid4())
        self.question = question.strip()
        self.state = InvestigationState.INITIALIZED
        self.created_at = datetime.utcnow()
        self.max_steps = max_steps
        self.evidence_store = EvidenceStore()
        self.planner: Optional[InvestigationPlanner] = None
        self.critic: Optional[AdversarialCritic] = None
        self.tool_registry = tool_registry or ToolRegistry()
        self.persistence = persistence
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.primary_hypothesis_id: Optional[str] = None
        self.steps_taken = 0
        self.observations_made: List[Observation] = []
        self.plan_history: List[Dict] = []
        self.tool_results: List[ToolResult] = []
        self.critique_history: List[str] = []

    def initialize_hypotheses(self, hypotheses: List[str]) -> None:
        if not hypotheses:
            raise ValueError("At least one hypothesis is required")
        for statement in hypotheses:
            if not statement or not statement.strip():
                continue
            hyp_id = str(uuid.uuid4())
            is_primary = not self.hypotheses
            self.hypotheses[hyp_id] = Hypothesis(
                id=hyp_id, statement=statement.strip(),
                created_at=datetime.utcnow(), is_primary=is_primary
            )
            if is_primary:
                self.primary_hypothesis_id = hyp_id
        if not self.hypotheses:
            raise ValueError("At least one non-empty hypothesis is required")

    def add_observation(self, source: EvidenceSource, raw_data: Any,
                        interpretation: str, confidence: ConfidenceLevel) -> Observation:
        obs = Observation(source=source, timestamp=datetime.utcnow(), raw_data=raw_data,
                          interpretation=interpretation, confidence=confidence)
        self.evidence_store.add_observation(obs)
        self.observations_made.append(obs)
        return obs

    def link_observation_to_hypothesis(self, observation: Observation, hypothesis_id: str,
                                       supporting: bool = True, strength: float = 0.5) -> None:
        if hypothesis_id not in self.hypotheses:
            raise KeyError(f"Unknown hypothesis: {hypothesis_id}")
        if not 0 <= strength <= 1:
            raise ValueError("strength must be between 0 and 1")
        evidence = self.evidence_store.evaluate_observation(
            observation,
            supports=[hypothesis_id] if supporting else [],
            contradicts=[] if supporting else [hypothesis_id],
            supporting_strength=strength if supporting else 0.0,
            contradicting_strength=0.0 if supporting else strength,
            analysis="",
        )
        hyp = self.hypotheses[hypothesis_id]
        target = hyp.supporting_evidence if supporting else hyp.contradicting_evidence
        if evidence not in target:
            target.append(evidence)
        hyp.confidence_score = hyp.calculate_confidence()

    def run(self) -> Verdict:
        if not self.hypotheses:
            raise ValueError("No hypotheses initialized. Call initialize_hypotheses() first.")
        self.planner = self.planner or InvestigationPlanner(self.id)
        self.critic = self.critic or AdversarialCritic(self.evidence_store)
        self.planner.initialize_plan(self.question, list(self.hypotheses.values()))

        while self.steps_taken < self.max_steps:
            self.state = InvestigationState.PLANNING
            plan_decision = self._plan_next_action()
            self.plan_history.append(plan_decision)
            if self._should_terminate():
                break

            self.state = InvestigationState.EXECUTING
            self._execute_planned_tools()
            self.state = InvestigationState.ANALYZING
            self._update_hypothesis_states()
            self._apply_critic()
            self.steps_taken += 1
            self._checkpoint()

            if self._should_terminate():
                break
            self.planner.replan(self.evidence_store, list(self.hypotheses.values()))

        self.state = InvestigationState.CONCLUDING
        verdict = self._generate_verdict()
        self.state = InvestigationState.COMPLETED
        self._checkpoint()
        return verdict

    def _plan_next_action(self) -> Dict:
        primary = self._get_primary_hypothesis()
        evidence_count = self.evidence_store.summary()["total_evidence"]
        if evidence_count < 2:
            action = "gather_initial_evidence"
        elif primary.confidence_score < 0.5:
            action = "test_alternative_hypotheses"
        elif primary.contradicting_evidence:
            action = "investigate_contradictions"
        else:
            action = "validate_hypothesis"
        tools = self.planner.decide_next_tools(
            self.evidence_store, list(self.hypotheses.values()), max_tools=3
        ) if self.planner else []
        return {
            "step": self.steps_taken, "action": action, "tools": tools,
            "timestamp": datetime.utcnow(),
            "rationale": f"Primary hypothesis confidence: {primary.confidence_score:.2f}",
        }

    def _execute_planned_tools(self) -> None:
        tool_names = self.plan_history[-1].get("tools", []) if self.plan_history else []
        for tool_name in tool_names:
            result = self.tool_registry.execute_tool(tool_name, **self._tool_kwargs(tool_name))
            self.tool_results.append(result)
            if not result.success:
                continue
            observation = result.to_observation(self._source_for_tool(tool_name))
            if observation is None:
                continue
            self.evidence_store.add_observation(observation)
            self.observations_made.append(observation)
            self._evaluate_tool_observation(observation)

    def _tool_kwargs(self, tool_name: str) -> Dict[str, Any]:
        tool = self.tool_registry.get_tool(tool_name)
        if tool is None:
            return {"query": self.question}
        try:
            params = tool.get_parameters() or {}
        except Exception:
            params = {}
        kwargs = {}
        for name in params:
            if name in {"query", "question", "topic", "symbol", "asset"}:
                kwargs[name] = self.question
        return kwargs

    @staticmethod
    def _source_for_tool(tool_name: str) -> EvidenceSource:
        return {
            "fetch_market_data": EvidenceSource.MARKET_DATA,
            "analyze_technical": EvidenceSource.TECHNICAL_ANALYSIS,
            "fetch_on_chain_metrics": EvidenceSource.ON_CHAIN,
            "fetch_social_sentiment": EvidenceSource.SOCIAL_SENTIMENT,
        }.get(tool_name, EvidenceSource.INFERENCE)

    def _evaluate_tool_observation(self, observation: Observation) -> None:
        hypotheses = list(self.hypotheses.values())
        if not hypotheses:
            return
        text = f"{observation.interpretation} {observation.raw_data}".lower()
        scored = []
        for hyp in hypotheses:
            tokens = [t.strip(".,:;!?()[]{}\"") for t in hyp.statement.lower().split() if len(t.strip(".,:;!?()[]{}\"")) > 3]
            overlap = sum(1 for token in tokens if token and token in text)
            scored.append((overlap, hyp))
        scored.sort(key=lambda item: item[0], reverse=True)
        best = scored[0][1]
        strength = 0.45 if scored[0][0] == 0 else min(0.85, 0.45 + 0.10 * scored[0][0])
        self.link_observation_to_hypothesis(observation, best.id, True, strength)

    def _should_terminate(self) -> bool:
        primary = self._get_primary_hypothesis()
        if primary.confidence_score > 0.85 and len(primary.supporting_evidence) >= 3 and not primary.contradicting_evidence:
            return True
        total = self.evidence_store.summary()["total_evidence"]
        return total >= 6 and primary.confidence_score > 0.65

    def _update_hypothesis_states(self) -> None:
        for hyp_id, hyp in self.hypotheses.items():
            supporting, contradicting = self.evidence_store.get_evidence_for_hypothesis(hyp_id)
            hyp.supporting_evidence = supporting
            hyp.contradicting_evidence = contradicting
            hyp.confidence_score = hyp.calculate_confidence()

    def _apply_critic(self) -> None:
        primary = self._get_primary_hypothesis()
        if self.critic:
            self.critique_history.extend(self.critic.challenge_hypothesis(primary))

    def _get_primary_hypothesis(self) -> Hypothesis:
        if self.primary_hypothesis_id in self.hypotheses:
            return self.hypotheses[self.primary_hypothesis_id]
        return max(self.hypotheses.values(), key=lambda h: h.confidence_score)

    def rank_hypotheses(self) -> List[Hypothesis]:
        return sorted(self.hypotheses.values(), key=lambda h: h.confidence_score, reverse=True)

    def _generate_verdict(self) -> Verdict:
        primary = self._get_primary_hypothesis()
        all_evidence = self.evidence_store.get_all_evidence()
        supporting = [e for e in all_evidence if primary.id in e.supports_hypotheses]
        contradicting = [e for e in all_evidence if primary.id in e.contradicts_hypotheses]
        return Verdict(
            investigation_id=self.id, primary_hypothesis=primary,
            confidence=primary.confidence_score,
            supporting_evidence_count=len(supporting),
            contradicting_evidence_count=len(contradicting),
            summary=f"Investigation into '{self.question}' completed in {self.steps_taken} steps.",
            key_findings=[f"Primary: {primary.statement}", f"Confidence: {primary.confidence_score:.0%}"],
            assumptions=["Tool outputs are treated as evidence, not truth", "Independent source agreement increases confidence"],
            what_would_change_mind=self._determine_mind_change(primary),
        )

    def _determine_mind_change(self, primary: Optional[Hypothesis]) -> str:
        if not primary:
            return "Any hypothesis with evidence would change conclusion."
        if primary.confidence_score < 0.6:
            return "Strong independent evidence for an alternative hypothesis would change the conclusion."
        return "Multiple independent sources contradicting the primary hypothesis would change the conclusion."

    def _checkpoint(self) -> bool:
        if self.persistence is None:
            return False
        try:
            from oracle.persistence import StateSerializer
            return bool(self.persistence.save_investigation(self.id, StateSerializer.serialize(self)))
        except Exception:
            return False

    def get_state(self) -> Dict:
        primary = self._get_primary_hypothesis()
        return {
            "id": self.id, "question": self.question, "state": self.state.value,
            "steps_taken": self.steps_taken,
            "primary_hypothesis": primary.statement if primary else None,
            "confidence": primary.confidence_score if primary else None,
            "evidence_count": self.evidence_store.summary()["total_evidence"],
            "hypotheses_count": len(self.hypotheses),
            "tools_executed": len(self.tool_results),
            "critiques": len(self.critique_history),
        }
