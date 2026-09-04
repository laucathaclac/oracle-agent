"""Regression tests for ORACLE's autonomous execution and weighted confidence."""

from oracle.engine import OracleInvestigation
from oracle.executor import Tool, ToolResult, ToolRegistry
from oracle.persistence import InMemoryPersistence
from oracle.types import EvidenceSource, ConfidenceLevel


class MarketTool(Tool):
    def __init__(self):
        super().__init__("fetch_market_data", "mock market data")

    def get_parameters(self):
        return {"query": str}

    def execute(self, **kwargs):
        return ToolResult(
            self.name,
            True,
            {"interpretation": "BTC market data supports bullish outlook", "confidence": "high"},
        )


class ChainTool(Tool):
    def __init__(self):
        super().__init__("fetch_on_chain_metrics", "mock on-chain")

    def get_parameters(self):
        return {"query": str}

    def execute(self, **kwargs):
        return ToolResult(
            self.name,
            True,
            {"interpretation": "on-chain activity supports bullish outlook", "confidence": "high"},
        )


def test_weighted_confidence_uses_source_and_observation_confidence():
    inv = OracleInvestigation("BTC bullish", max_steps=1)
    inv.initialize_hypotheses(["BTC bullish"])
    obs = inv.add_observation(EvidenceSource.MARKET_DATA, {}, "supports", ConfidenceLevel.HIGH)
    inv.link_observation_to_hypothesis(obs, inv.primary_hypothesis_id, True, 0.8)
    assert inv._get_primary_hypothesis().confidence_score > 0.5


def test_engine_executes_planned_tools_and_persists():
    registry = ToolRegistry()
    registry.register(MarketTool())
    registry.register(ChainTool())
    persistence = InMemoryPersistence()
    inv = OracleInvestigation(
        "BTC bullish", max_steps=2, tool_registry=registry, persistence=persistence
    )
    inv.initialize_hypotheses(["BTC bullish", "BTC bearish"])

    verdict = inv.run()

    assert len(inv.tool_results) >= 1
    assert any(result.success for result in inv.tool_results)
    assert inv.evidence_store.summary()["total_evidence"] >= 1
    assert persistence.load_investigation(inv.id) is not None
    assert verdict.primary_hypothesis is not None
