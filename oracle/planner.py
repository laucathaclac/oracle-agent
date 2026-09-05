"""Investigation planner for autonomous decision-making."""

from typing import List, Dict, Set, Optional
from datetime import datetime
from oracle.types import InvestigationPlan, Hypothesis
from oracle.evidence_store import EvidenceStore


class InvestigationPlanner:
    """Plans investigation steps dynamically based on hypotheses and evidence."""

    def __init__(self, investigation_id: str):
        self.investigation_id = investigation_id
        self.plan: InvestigationPlan = InvestigationPlan(investigation_id=investigation_id)
        self.executed_tools: Set[str] = set()

    def initialize_plan(self, initial_question: str, initial_hypotheses: List[Hypothesis]) -> InvestigationPlan:
        """Create initial investigation plan."""
        self.plan.active_hypotheses = [h.id for h in initial_hypotheses]
        self.plan.rationale = f"Investigating: {initial_question}"
        self.plan.steps = self._generate_initial_steps(initial_hypotheses)
        self.plan.updated_at = datetime.utcnow()
        return self.plan

    def _generate_initial_steps(self, hypotheses: List[Hypothesis]) -> List[str]:
        return [
            "Step 1: Gather initial market data",
            "Step 2: Analyze technical indicators",
            "Step 3: Review on-chain metrics",
            "Step 4: Assess social sentiment",
            "Step 5: Evaluate hypothesis fitness",
        ]

    def decide_next_tools(
        self,
        evidence_store: EvidenceStore,
        hypotheses: List[Hypothesis],
        max_tools: int = 3,
        available_tools: Optional[List[Dict]] = None,
    ) -> List[str]:
        """Choose tools from evidence gaps and optional registry metadata.

        ``available_tools`` preserves backwards compatibility while allowing a
        live Agent OS/MCP registry to expose dynamically named tools.
        """
        next_tools: List[str] = []
        sources_used = set(evidence_store.summary()["sources"].keys())
        all_sources = {"market_data", "technical_analysis", "on_chain", "social_sentiment"}
        missing_sources = all_sources - sources_used

        default_mapping = {
            "market_data": "fetch_market_data",
            "technical_analysis": "analyze_technical",
            "on_chain": "fetch_on_chain_metrics",
            "social_sentiment": "fetch_social_sentiment",
        }
        tag_candidates: Dict[str, List[str]] = {source: [] for source in all_sources}
        if available_tools:
            for tool in available_tools:
                name = tool.get("name")
                tags = set(tool.get("tags", []))
                for source in all_sources:
                    if source in tags and name:
                        tag_candidates[source].append(name)

        for source in sorted(missing_sources):
            candidates = tag_candidates.get(source) or [default_mapping[source]]
            for tool in candidates:
                if len(next_tools) >= max_tools:
                    break
                if tool not in self.executed_tools:
                    next_tools.append(tool)
                    self.executed_tools.add(tool)
            if len(next_tools) >= max_tools:
                break

        if len(next_tools) < max_tools:
            low_confidence = [h for h in hypotheses if h.confidence_score < 0.6]
            if low_confidence and "evaluate_hypothesis_fitness" not in self.executed_tools:
                if not available_tools or any(t.get("name") == "evaluate_hypothesis_fitness" for t in available_tools):
                    next_tools.append("evaluate_hypothesis_fitness")
                    self.executed_tools.add("evaluate_hypothesis_fitness")

        self.plan.next_tools_to_invoke = next_tools[:max_tools]
        self.plan.updated_at = datetime.utcnow()
        return self.plan.next_tools_to_invoke

    def replan(
        self,
        evidence_store: EvidenceStore,
        hypotheses: List[Hypothesis],
        available_tools: Optional[List[Dict]] = None,
    ) -> InvestigationPlan:
        """Replan investigation based on new evidence."""
        self.plan.current_step += 1
        next_tools = self.decide_next_tools(
            evidence_store, hypotheses, available_tools=available_tools
        )
        self.plan.rationale = f"Replanning after step {self.plan.current_step}. Next tools: {next_tools}"
        self.plan.updated_at = datetime.utcnow()
        return self.plan

    def get_plan(self) -> InvestigationPlan:
        return self.plan
