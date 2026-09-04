from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Dict, List
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Confidence levels for observations and hypotheses."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class EvidenceSource(str, Enum):
    """Source types for evidence."""
    BINANCE_API = "binance_api"
    MARKET_DATA = "market_data"
    ON_CHAIN = "on_chain"
    SOCIAL_SENTIMENT = "social_sentiment"
    NEWS = "news"
    TECHNICAL_ANALYSIS = "technical_analysis"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    CRITIC = "critic"


class InvestigationState(str, Enum):
    """Investigation lifecycle states."""
    INITIALIZED = "initialized"
    PLANNING = "planning"
    EXECUTING = "executing"
    ANALYZING = "analyzing"
    CONCLUDING = "concluding"
    COMPLETED = "completed"
    PAUSED = "paused"


@dataclass
class Observation:
    """Raw observation from a tool or data source."""
    source: EvidenceSource
    timestamp: datetime
    raw_data: Any
    interpretation: str
    confidence: ConfidenceLevel
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.source, self.timestamp, str(self.raw_data)))


@dataclass
class Evidence:
    """Evaluated evidence with supporting/contradicting information."""
    observation: Observation
    supports_hypotheses: List[str] = field(default_factory=list)
    contradicts_hypotheses: List[str] = field(default_factory=list)
    supporting_strength: float = 0.5
    contradicting_strength: float = 0.0
    analysis: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Hypothesis:
    """Competing hypothesis with evidence tracking."""
    id: str
    statement: str
    created_at: datetime
    supporting_evidence: List[Evidence] = field(default_factory=list)
    contradicting_evidence: List[Evidence] = field(default_factory=list)
    confidence_score: float = 0.5
    is_primary: bool = False
    rationale: str = ""

    # Reliability priors: objective/direct data gets more weight than inference.
    _SOURCE_WEIGHTS = {
        EvidenceSource.BINANCE_API: 1.00,
        EvidenceSource.MARKET_DATA: 0.95,
        EvidenceSource.ON_CHAIN: 0.95,
        EvidenceSource.TECHNICAL_ANALYSIS: 0.85,
        EvidenceSource.NEWS: 0.80,
        EvidenceSource.SOCIAL_SENTIMENT: 0.60,
        EvidenceSource.INFERENCE: 0.55,
        EvidenceSource.HYPOTHESIS: 0.40,
        EvidenceSource.CRITIC: 0.75,
    }
    _CONFIDENCE_WEIGHTS = {
        ConfidenceLevel.VERY_LOW: 0.25,
        ConfidenceLevel.LOW: 0.50,
        ConfidenceLevel.MEDIUM: 0.75,
        ConfidenceLevel.HIGH: 1.00,
        ConfidenceLevel.VERY_HIGH: 1.10,
    }

    @classmethod
    def _evidence_weight(cls, evidence: Evidence, supporting: bool) -> float:
        strength = evidence.supporting_strength if supporting else evidence.contradicting_strength
        source_weight = cls._SOURCE_WEIGHTS.get(evidence.observation.source, 0.70)
        confidence_weight = cls._CONFIDENCE_WEIGHTS.get(evidence.observation.confidence, 0.75)
        return max(0.0, min(1.0, strength)) * source_weight * confidence_weight

    def calculate_confidence(self) -> float:
        """Calculate confidence from strength, source reliability and observation confidence."""
        if not self.supporting_evidence and not self.contradicting_evidence:
            return 0.5

        support = sum(self._evidence_weight(e, True) for e in self.supporting_evidence)
        contradict = sum(self._evidence_weight(e, False) for e in self.contradicting_evidence)
        total = support + contradict
        if total <= 0:
            return 0.5
        return max(0.0, min(1.0, support / total))


@dataclass
class InvestigationPlan:
    """Investigation action plan."""
    investigation_id: str
    current_step: int = 0
    steps: List[str] = field(default_factory=list)
    active_hypotheses: List[str] = field(default_factory=list)
    next_tools_to_invoke: List[str] = field(default_factory=list)
    rationale: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Verdict:
    """Final investigation verdict."""
    investigation_id: str
    primary_hypothesis: Optional[Hypothesis]
    confidence: float
    supporting_evidence_count: int
    contradicting_evidence_count: int
    summary: str
    key_findings: List[str]
    assumptions: List[str]
    what_would_change_mind: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class InvestigationMemory:
    """Memory of a completed investigation."""
    id: str
    question: str
    timestamp: datetime
    primary_hypothesis: str
    outcome: str
    confidence: float
    post_mortem: str
    duration_seconds: float
