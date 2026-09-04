"""Core data types for ORACLE agent."""

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
    supports_hypotheses: List[str] = field(default_factory=list)  # hypothesis IDs
    contradicts_hypotheses: List[str] = field(default_factory=list)  # hypothesis IDs
    supporting_strength: float = 0.5  # 0-1 scale
    contradicting_strength: float = 0.0  # 0-1 scale
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
    confidence_score: float = 0.5  # 0-1 scale
    is_primary: bool = False
    rationale: str = ""

    def calculate_confidence(self) -> float:
        """Calculate confidence based on evidence balance."""
        if not self.supporting_evidence and not self.contradicting_evidence:
            return 0.5
        
        support_score = sum(e.supporting_strength for e in self.supporting_evidence)
        contradict_score = sum(e.contradicting_strength for e in self.contradicting_evidence)
        
        total = support_score + contradict_score
        if total == 0:
            return 0.5
        
        return support_score / total


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
