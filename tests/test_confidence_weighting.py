"""Tests for source-aware confidence weighting and the demo path."""

from oracle.demo_tools import build_demo_registry
from oracle.engine import OracleInvestigation
from oracle.types import EvidenceSource, ConfidenceLevel, Evidence, Observation, Hypothesis
from datetime import datetime


def _evidence(source, confidence, strength, hypothesis_id, supporting=True):
    observation = Observation(
        source=source,
        timestamp=datetime.utcnow(),
        raw_data={},
        interpretation="test",
        confidence=confidence,
    )
    return Evidence(
        observation=observation,
        supports_hypotheses=[hypothesis_id] if supporting else [],
        contradicts_hypotheses=[] if supporting else [hypothesis_id],
        supporting_strength=strength if supporting else 0.0,
        contradicting_strength=0.0 if supporting else strength,
    )


def test_high_quality_source_outweighs_low_quality_source():
    hyp = Hypothesis("h", "BTC is bullish", datetime.utcnow())
    hyp.supporting_evidence.append(
        _evidence(EvidenceSource.MARKET_DATA, ConfidenceLevel.HIGH, 0.8, hyp.id)
    )
    hyp.contradicting_evidence.append(
        _evidence(EvidenceSource.SOCIAL_SENTIMENT, ConfidenceLevel.MEDIUM, 0.8, hyp.id, False)
    )
    assert hyp.calculate_confidence() > 0.5


def test_confidence_stays_bounded():
    hyp = Hypothesis("h", "BTC is bullish", datetime.utcnow())
    hyp.supporting_evidence.append(
        _evidence(EvidenceSource.BINANCE_API, ConfidenceLevel.VERY_HIGH, 1.0, hyp.id)
    )
    assert 0.0 <= hyp.calculate_confidence() <= 1.0


def test_demo_executes_tools_and_persists_state():
    investigation = OracleInvestigation(
        "Is BTC market structure bullish?",
        max_steps=4,
        tool_registry=build_demo_registry(),
    )
    investigation.initialize_hypotheses([
        "BTC market structure is bullish",
        "BTC market structure is bearish",
        "BTC market structure is neutral",
    ])
    verdict = investigation.run()
    assert investigation.state.value == "completed"
    assert len(investigation.tool_results) > 0
    assert verdict.primary_hypothesis is not None
