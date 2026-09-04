"""Deterministic demo tools for showcasing ORACLE without API keys.

These tools model the interface that live Binance Agent OS/MCP tools can satisfy.
They intentionally use synthetic observations so the repository remains safe and
reproducible for reviewers.
"""

from typing import Dict

from oracle.executor import Tool, ToolResult, ToolRegistry


class StaticResearchTool(Tool):
    """A deterministic research tool backed by a supplied result payload."""

    def __init__(self, name: str, description: str, payload: Dict):
        super().__init__(name, description, tags=["demo", "research"])
        self.payload = payload

    def execute(self, **kwargs) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            success=True,
            data=dict(self.payload),
        )

    def get_parameters(self):
        return {"query": str}


def build_demo_registry() -> ToolRegistry:
    """Build a reproducible registry covering four evidence domains."""
    registry = ToolRegistry()
    registry.register(StaticResearchTool(
        "fetch_market_data",
        "Read market structure and price momentum.",
        {
            "interpretation": "BTC market structure is bullish with positive momentum.",
            "confidence": "high",
            "price_change_24h": 3.4,
        },
    ))
    registry.register(StaticResearchTool(
        "analyze_technical",
        "Evaluate trend and momentum indicators.",
        {
            "interpretation": "Technical trend remains bullish; momentum is positive.",
            "confidence": "high",
            "trend": "bullish",
        },
    ))
    registry.register(StaticResearchTool(
        "fetch_on_chain_metrics",
        "Inspect aggregate on-chain positioning.",
        {
            "interpretation": "On-chain activity is constructive but not conclusive.",
            "confidence": "medium",
            "activity": "constructive",
        },
    ))
    registry.register(StaticResearchTool(
        "fetch_social_sentiment",
        "Assess broad social sentiment.",
        {
            "interpretation": "Social sentiment is mixed, adding a mild counter-signal.",
            "confidence": "medium",
            "sentiment": "mixed",
        },
    ))
    return registry
