"""Run ORACLE against live Binance Agent OS market-data tools.

This path is intentionally separate from demo.py. The default demo remains
fully deterministic and does not need network access, credentials, or funds.
"""

import argparse

from oracle.binance_agent_os import BinanceAgentOSClient, build_binance_agent_os_registry
from oracle.engine import OracleInvestigation


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ORACLE with Binance Agent OS")
    parser.add_argument("--question", default="Is BTC market structure bullish?")
    parser.add_argument("--symbol", default="BTCUSDT", help="Market symbol used by the adapter defaults")
    parser.add_argument("--max-steps", type=int, default=3)
    args = parser.parse_args()

    # The current ORACLE Tool contract uses BTCUSDT as the safe default. The
    # question remains the agent's reasoning target; the adapter maps the
    # market symbol into compatible MCP schemas.
    client = BinanceAgentOSClient()
    registry = build_binance_agent_os_registry(client=client)

    print("=== ORACLE × BINANCE AGENT OS ===")
    print(f"MCP endpoint: {client.url}")
    print(f"Registered read-only tools: {', '.join(registry.tools)}")
    print(f"Question: {args.question}")

    investigation = OracleInvestigation(
        args.question,
        max_steps=args.max_steps,
        tool_registry=registry,
    )
    investigation.initialize_hypotheses([
        "BTC market structure is bullish",
        "BTC market structure is bearish",
        "BTC market structure is neutral",
    ])
    verdict = investigation.run()

    print("\n=== ORACLE VERDICT ===")
    print(f"Conclusion: {verdict.primary_hypothesis.statement}")
    print(f"Confidence: {verdict.confidence:.0%}")
    print(f"Evidence: +{verdict.supporting_evidence_count} / -{verdict.contradicting_evidence_count}")
    print(f"Tools: {len(investigation.tool_results)}")
    print(f"Critiques: {len(investigation.critique_history)}")
    print(f"Reversal condition: {verdict.what_would_change_mind}")


if __name__ == "__main__":
    main()
