"""Tests for ORACLE core investigation engine."""

import pytest
from datetime import datetime
from oracle.engine import OracleInvestigation
from oracle.types import EvidenceSource, ConfidenceLevel, InvestigationState


def test_investigation_initialization():
    """Test that investigation initializes correctly."""
    investigation = OracleInvestigation("Is the market bullish?", max_steps=5)

    assert investigation.question == "Is the market bullish?"
    assert investigation.state == InvestigationState.INITIALIZED
    assert investigation.steps_taken == 0
    assert len(investigation.hypotheses) == 0


def test_initialize_hypotheses():
    """Test hypothesis initialization."""
    investigation = OracleInvestigation("Test question")
    hypotheses = ["Market is bullish", "Market is bearish", "Market is sideways"]

    investigation.initialize_hypotheses(hypotheses)

    assert len(investigation.hypotheses) == 3
    assert investigation.primary_hypothesis_id is not None
    assert investigation.hypotheses[investigation.primary_hypothesis_id].statement == "Market is bullish"
    assert investigation.hypotheses[investigation.primary_hypothesis_id].is_primary is True


def test_add_observation():
    """Test adding observations to investigation."""
    investigation = OracleInvestigation("Test question")
    investigation.initialize_hypotheses(["Test hypothesis"])

    obs = investigation.add_observation(
        source=EvidenceSource.MARKET_DATA,
        raw_data={"price": 100},
        interpretation="Price is rising",
        confidence=ConfidenceLevel.HIGH,
    )

    assert obs.source == EvidenceSource.MARKET_DATA
    assert obs.interpretation == "Price is rising"
    assert len(investigation.observations_made) == 1


def test_link_observation_to_hypothesis_supporting():
    """Test linking observation as supporting evidence."""
    investigation = OracleInvestigation("Test question")
    hypotheses = ["Market is bullish", "Market is bearish"]
    investigation.initialize_hypotheses(hypotheses)

    obs = investigation.add_observation(
        source=EvidenceSource.MARKET_DATA,
        raw_data={"price": 100},
        interpretation="Price rose",
        confidence=ConfidenceLevel.HIGH,
    )

    primary_id = investigation.primary_hypothesis_id
    investigation.link_observation_to_hypothesis(
        obs, primary_id, supporting=True, strength=0.8
    )

    primary_hyp = investigation.hypotheses[primary_id]
    assert len(primary_hyp.supporting_evidence) == 1
    assert len(primary_hyp.contradicting_evidence) == 0
    assert primary_hyp.confidence_score > 0.5


def test_link_observation_to_hypothesis_contradicting():
    """Test linking observation as contradicting evidence."""
    investigation = OracleInvestigation("Test question")
    investigation.initialize_hypotheses(["Market is bullish"])

    obs = investigation.add_observation(
        source=EvidenceSource.MARKET_DATA,
        raw_data={"price": 50},
        interpretation="Price fell sharply",
        confidence=ConfidenceLevel.HIGH,
    )

    primary_id = investigation.primary_hypothesis_id
    investigation.link_observation_to_hypothesis(
        obs, primary_id, supporting=False, strength=0.7
    )

    primary_hyp = investigation.hypotheses[primary_id]
    assert len(primary_hyp.contradicting_evidence) == 1
    assert len(primary_hyp.supporting_evidence) == 0
    assert primary_hyp.confidence_score < 0.5


def test_confidence_decreases_with_contradicting_evidence():
    """Test that contradicting evidence lowers hypothesis confidence."""
    investigation = OracleInvestigation("Test question")
    investigation.initialize_hypotheses(["Market is bullish"])
    primary_id = investigation.primary_hypothesis_id

    # Add supporting evidence
    obs_support = investigation.add_observation(
        source=EvidenceSource.MARKET_DATA,
        raw_data={"price": 100},
        interpretation="Price is rising",
        confidence=ConfidenceLevel.HIGH,
    )
    investigation.link_observation_to_hypothesis(
        obs_support, primary_id, supporting=True, strength=0.9
    )

    confidence_after_support = investigation.hypotheses[primary_id].confidence_score

    # Add contradicting evidence
    obs_contradict = investigation.add_observation(
        source=EvidenceSource.NEWS,
        raw_data={"headline": "Regulatory crackdown"},
        interpretation="Bearish news",
        confidence=ConfidenceLevel.HIGH,
    )
    investigation.link_observation_to_hypothesis(
        obs_contradict, primary_id, supporting=False, strength=0.8
    )

    confidence_after_contradict = investigation.hypotheses[primary_id].confidence_score

    # Confidence should decrease
    assert confidence_after_contradict < confidence_after_support


def test_planner_chooses_different_actions():
    """Test that planner dynamically chooses different next actions based on evidence."""
    investigation = OracleInvestigation("Test question", max_steps=10)
    investigation.initialize_hypotheses(["Hypothesis A", "Hypothesis B"])

    # First decision: no evidence, should gather
    decision1 = investigation._plan_next_action()
    assert decision1["action"] == "gather_initial_evidence"

    # Add some evidence
    obs = investigation.add_observation(
        source=EvidenceSource.MARKET_DATA,
        raw_data={"data": "value"},
        interpretation="Some data",
        confidence=ConfidenceLevel.MEDIUM,
    )
    investigation.link_observation_to_hypothesis(
        obs,
        investigation.primary_hypothesis_id,
        supporting=True,
        strength=0.6,
    )
    investigation._update_hypothesis_states()

    # Second decision: with evidence but low confidence, might test alternatives
    decision2 = investigation._plan_next_action()
    # Could be "test_alternative_hypotheses" or "validate_hypothesis"
    assert decision2["action"] in [
        "gather_initial_evidence",
        "test_alternative_hypotheses",
        "validate_hypothesis",
    ]


def test_critic_challenges_hypothesis():
    """Test that adversarial critic challenges the leading hypothesis."""
    investigation = OracleInvestigation("Test question")
    investigation.initialize_hypotheses(["Market is bullish"])
    investigation.planner = investigation.planner or None
    investigation.critic = investigation.critic or None

    # Initialize critic
    from oracle.critic import AdversarialCritic

    investigation.critic = AdversarialCritic(investigation.evidence_store)

    primary = investigation._get_primary_hypothesis()

    # Critic should challenge hypothesis with no evidence
    challenges = investigation.critic.challenge_hypothesis(primary)
    assert len(challenges) > 0
    assert any("no supporting evidence" in c.lower() for c in challenges)


def test_investigation_run_complete_loop():
    """Test full investigation loop execution."""
    investigation = OracleInvestigation("Is market bullish?", max_steps=5)
    investigation.initialize_hypotheses(["Bullish", "Bearish", "Neutral"])

    # Add some observations
    obs1 = investigation.add_observation(
        source=EvidenceSource.MARKET_DATA,
        raw_data={"price": 150},
        interpretation="Price increased",
        confidence=ConfidenceLevel.HIGH,
    )

    obs2 = investigation.add_observation(
        source=EvidenceSource.TECHNICAL_ANALYSIS,
        raw_data={"signal": "buy"},
        interpretation="Technical indicators positive",
        confidence=ConfidenceLevel.MEDIUM,
    )

    # Link to hypotheses
    primary_id = investigation.primary_hypothesis_id
    investigation.link_observation_to_hypothesis(
        obs1, primary_id, supporting=True, strength=0.8
    )
    investigation.link_observation_to_hypothesis(
        obs2, primary_id, supporting=True, strength=0.7
    )

    # Run investigation
    verdict = investigation.run()

    # Verify verdict
    assert verdict.investigation_id == investigation.id
    assert verdict.primary_hypothesis is not None
    assert verdict.supporting_evidence_count >= 2
    assert investigation.state == InvestigationState.COMPLETED


def test_investigation_terminates_with_high_confidence():
    """Test that investigation terminates when high confidence is reached."""
    investigation = OracleInvestigation("Test", max_steps=20)
    investigation.initialize_hypotheses(["Hypothesis"])
    primary_id = investigation.primary_hypothesis_id

    # Add strong supporting evidence
    for i in range(5):
        obs = investigation.add_observation(
            source=EvidenceSource.MARKET_DATA,
            raw_data={"data": i},
            interpretation=f"Evidence {i}",
            confidence=ConfidenceLevel.VERY_HIGH,
        )
        investigation.link_observation_to_hypothesis(
            obs, primary_id, supporting=True, strength=0.95
        )

    investigation._update_hypothesis_states()

    # Should terminate early due to high confidence
    verdict = investigation.run()
    assert investigation.steps_taken < 20  # Should stop before max_steps
    assert verdict.confidence > 0.7


def test_investigation_handles_contradictions():
    """Test that investigation properly handles contradicting evidence."""
    investigation = OracleInvestigation("Test", max_steps=10)
    investigation.initialize_hypotheses(["Bullish"])
    primary_id = investigation.primary_hypothesis_id

    # Add supporting evidence
    obs_support = investigation.add_observation(
        source=EvidenceSource.MARKET_DATA,
        raw_data={"trend": "up"},
        interpretation="Uptrend",
        confidence=ConfidenceLevel.HIGH,
    )
    investigation.link_observation_to_hypothesis(
        obs_support, primary_id, supporting=True, strength=0.8
    )

    # Add contradicting evidence
    obs_contradict = investigation.add_observation(
        source=EvidenceSource.NEWS,
        raw_data={"event": "crash"},
        interpretation="Market crash",
        confidence=ConfidenceLevel.HIGH,
    )
    investigation.link_observation_to_hypothesis(
        obs_contradict, primary_id, supporting=False, strength=0.8
    )

    investigation._update_hypothesis_states()

    # Run investigation - should detect contradiction
    verdict = investigation.run()

    assert verdict.contradicting_evidence_count > 0
    assert verdict.supporting_evidence_count > 0
    # Confidence should be moderate due to contradiction
    assert 0.3 < verdict.confidence < 0.7


def test_investigation_state_transitions():
    """Test that investigation moves through states correctly."""
    investigation = OracleInvestigation("Test")
    investigation.initialize_hypotheses(["Test"])

    assert investigation.state == InvestigationState.INITIALIZED

    # Manually transition through states
    investigation.state = InvestigationState.PLANNING
    assert investigation.state == InvestigationState.PLANNING

    investigation.state = InvestigationState.EXECUTING
    assert investigation.state == InvestigationState.EXECUTING

    investigation.state = InvestigationState.ANALYZING
    assert investigation.state == InvestigationState.ANALYZING

    # Run to completion
    verdict = investigation.run()
    assert investigation.state == InvestigationState.COMPLETED


def test_get_state_returns_correct_summary():
    """Test that get_state returns accurate investigation summary."""
    investigation = OracleInvestigation("Test question")
    investigation.initialize_hypotheses(["Hypothesis A", "Hypothesis B"])

    obs = investigation.add_observation(
        source=EvidenceSource.MARKET_DATA,
        raw_data={"value": 1},
        interpretation="Test",
        confidence=ConfidenceLevel.MEDIUM,
    )
    investigation.link_observation_to_hypothesis(
        obs,
        investigation.primary_hypothesis_id,
        supporting=True,
        strength=0.7,
    )

    state = investigation.get_state()

    assert state["question"] == "Test question"
    assert state["hypotheses_count"] == 2
    assert state["evidence_count"] == 1
    assert state["confidence"] is not None
    assert state["primary_hypothesis"] == "Hypothesis A"


def test_multiple_hypotheses_ranked_by_confidence():
    """Test that multiple hypotheses are ranked by confidence score."""
    investigation = OracleInvestigation("Test")
    investigation.initialize_hypotheses(["Hypothesis A", "Hypothesis B", "Hypothesis C"])

    hyp_ids = list(investigation.hypotheses.keys())

    # Add evidence favoring different hypotheses
    obs1 = investigation.add_observation(
        source=EvidenceSource.MARKET_DATA,
        raw_data={"data": 1},
        interpretation="Test 1",
        confidence=ConfidenceLevel.HIGH,
    )

    obs2 = investigation.add_observation(
        source=EvidenceSource.TECHNICAL_ANALYSIS,
        raw_data={"data": 2},
        interpretation="Test 2",
        confidence=ConfidenceLevel.MEDIUM,
    )

    # Strong evidence for first hypothesis
    investigation.link_observation_to_hypothesis(
        obs1, hyp_ids[0], supporting=True, strength=0.9
    )
    # Weak evidence for second hypothesis
    investigation.link_observation_to_hypothesis(
        obs2, hyp_ids[1], supporting=True, strength=0.4
    )

    investigation._update_hypothesis_states()

    # First hypothesis should have highest confidence
    primary = investigation._get_primary_hypothesis()
    assert primary.id == hyp_ids[0]
    assert primary.confidence_score > investigation.hypotheses[hyp_ids[1]].confidence_score
