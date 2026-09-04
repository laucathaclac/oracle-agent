"""Run the ORACLE deterministic end-to-end demo.

Usage:
    python demo.py
"""

from oracle.demo_tools import build_demo_registry
from oracle.engine import OracleInvestigation
from oracle.persistence import InMemoryPersistence


def main() -> None:
    registry = build_demo_registry()
    memory = InMemoryPersistence()

    investigation = OracleInvestigation(
        "Is BTC market structure bullish?",
        max_steps=4,
        tool_registry=registry,
        persistence=memory,
    )
    investigation.initialize_hypotheses([
        "BTC market structure is bullish",
        "BTC market structure is bearish",
        "BTC market structure is neutral",
    ])

    verdict = investigation.run()

    print("\n=== ORACLE VERDICT ===")
    print(f"Question:    {investigation.question}")
    print(f"Conclusion:  {verdict.primary_hypothesis.statement}")
    print(f"Confidence:  {verdict.confidence:.1%}")
    print(f"Evidence:    +{verdict.supporting_evidence_count} / -{verdict.contradicting_evidence_count}")
    print(f"Tools:       {len(investigation.tool_results)}")
    print(f"Critiques:   {len(investigation.critique_history)}")
    print(f"Checkpoints: {memory.list_investigations()}")
    print(f"Reversal:    {verdict.what_would_change_mind}")


if __name__ == "__main__":
    main()
