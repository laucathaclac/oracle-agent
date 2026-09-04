"""Investigation planner for autonomous decision-making."""

from typing import List, Dict, Set
from datetime import datetime
from oracle.types import InvestigationPlan, Hypothesis
from oracle.evidence_store import EvidenceStore


class InvestigationPlanner:
    """Plans investigation steps dynamically based on hypotheses and evidence."""

    def __init__(self, investigation_id: str):
        self.investigation_id = investigation_id
        self.plan: InvestigationPlan = InvestigationPlan(
            investigation_id=investigation_id
        )
        self.executed_tools: Set[str] = set()

    def initialize_plan(
        self,
        initial_question: str,
        initial_hypotheses: List[Hypothesis],
    ) -> InvestigationPlan:
        """Create initial investigation plan."""
        self.plan.active_hypotheses = [h.id for h in initial_hypotheses]
        self.plan.rationale = f"Investigating: {initial_question}"
        self.plan.steps = self._generate_initial_steps(initial_hypotheses)
        self.plan.updated_at = datetime.utcnow()
        return self.plan

    def _generate_initial_steps(self, hypotheses: List[Hypothesis]) -> List[str]:
        """Generate initial investigation steps."""
        steps = [
            "Step 1: Gather initial market data",
            "Step 2: Analyze technical indicators",
            "Step 3: Review on-chain metrics",
            "Step 4: Assess social sentiment",
            "Step 5: Evaluate hypothesis fitness",
        ]
        return steps

    def decide_next_tools(
        self,
        evidence_store: EvidenceStore,
        hypotheses: List[Hypothesis],
        max_tools: int = 3,
    ) -> List[str]:
        """Decide which tools to invoke next based on evidence gaps."""
        next_tools = []

        # Identify evidence gaps
        evidence_summary = evidence_store.summary()
        sources_used = set(evidence_summary["sources"].keys())

        # Recommend tools for sources not yet explored
        all_sources = {
            "market_data",
            "technical_analysis",
            "on_chain",
            "social_sentiment",
        }
        missing_sources = all_sources - sources_used

        tool_mapping = {
            "market_data": "fetch_market_data",
            "technical_analysis": "analyze_technical",
            "on_chain": "fetch_on_chain_metrics",
            "social_sentiment": "fetch_social_sentiment",
        }

        for source in list(missing_sources)[: max_tools - len(next_tools)]:
            if source in tool_mapping:
                tool = tool_mapping[source]
                if tool not in self.executed_tools:
                    next_tools.append(tool)
                    self.executed_tools.add(tool)

        # If we need more tools, recommend hypothesis refinement
        if len(next_tools) < max_tools:
            low_confidence_hypotheses = [
                h for h in hypotheses if h.confidence_score < 0.6
            ]
            if low_confidence_hypotheses:
                next_tools.append("evaluate_hypothesis_fitness")

        self.plan.next_tools_to_invoke = next_tools[: max_tools]
        self.plan.updated_at = datetime.utcnow()
        return self.plan.next_tools_to_invoke

    def replan(
        self,
        evidence_store: EvidenceStore,
        hypotheses: List[Hypothesis],
    ) -> InvestigationPlan:
        """Replan investigation based on new evidence."""
        self.plan.current_step += 1
        next_tools = self.decide_next_tools(evidence_store, hypotheses)
        self.plan.rationale = f"Replanning after step {self.plan.current_step}. Next tools: {next_tools}"
        self.plan.updated_at = datetime.utcnow()
        return self.plan

    def get_plan(self) -> InvestigationPlan:
        """Get current plan."""
        return self.plan
