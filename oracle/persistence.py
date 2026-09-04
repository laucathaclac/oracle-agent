"""Investigation state persistence abstraction."""

import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path


class PersistenceBackend(ABC):
    """Abstract base for investigation state persistence."""

    @abstractmethod
    def save_investigation(self, investigation_id: str, state: Dict[str, Any]) -> bool:
        """Save investigation state. Returns success flag."""
        pass

    @abstractmethod
    def load_investigation(self, investigation_id: str) -> Optional[Dict[str, Any]]:
        """Load investigation state. Returns None if not found."""
        pass

    @abstractmethod
    def delete_investigation(self, investigation_id: str) -> bool:
        """Delete investigation state. Returns success flag."""
        pass

    @abstractmethod
    def list_investigations(self) -> list:
        """List all saved investigation IDs."""
        pass


class InMemoryPersistence(PersistenceBackend):
    """In-memory persistence for testing."""

    def __init__(self):
        self.store: Dict[str, Dict[str, Any]] = {}
        self.access_log: list = []

    def save_investigation(self, investigation_id: str, state: Dict[str, Any]) -> bool:
        """Save to memory."""
        try:
            self.store[investigation_id] = {
                "state": json.loads(json.dumps(state, default=str)),  # Deep copy with serialization check
                "saved_at": datetime.utcnow().isoformat(),
            }
            self.access_log.append({"action": "save", "id": investigation_id, "timestamp": datetime.utcnow()})
            return True
        except Exception as e:
            self.access_log.append({"action": "save_error", "id": investigation_id, "error": str(e)})
            return False

    def load_investigation(self, investigation_id: str) -> Optional[Dict[str, Any]]:
        """Load from memory."""
        self.access_log.append({"action": "load", "id": investigation_id, "timestamp": datetime.utcnow()})
        if investigation_id in self.store:
            return self.store[investigation_id]["state"]
        return None

    def delete_investigation(self, investigation_id: str) -> bool:
        """Delete from memory."""
        try:
            if investigation_id in self.store:
                del self.store[investigation_id]
            self.access_log.append({"action": "delete", "id": investigation_id, "timestamp": datetime.utcnow()})
            return True
        except Exception:
            return False

    def list_investigations(self) -> list:
        """List all investigation IDs."""
        return list(self.store.keys())

    def clear(self):
        """Clear all stored investigations."""
        self.store.clear()


class FilePersistence(PersistenceBackend):
    """File-based persistence using JSON."""

    def __init__(self, directory: str = ".oracle_state"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _get_filepath(self, investigation_id: str) -> Path:
        """Get filepath for investigation."""
        return self.directory / f"{investigation_id}.json"

    def save_investigation(self, investigation_id: str, state: Dict[str, Any]) -> bool:
        """Save to JSON file."""
        try:
            filepath = self._get_filepath(investigation_id)
            data = {
                "id": investigation_id,
                "state": state,
                "saved_at": datetime.utcnow().isoformat(),
            }
            with open(filepath, "w") as f:
                json.dump(data, f, default=str, indent=2)
            return True
        except Exception:
            return False

    def load_investigation(self, investigation_id: str) -> Optional[Dict[str, Any]]:
        """Load from JSON file."""
        try:
            filepath = self._get_filepath(investigation_id)
            if not filepath.exists():
                return None
            with open(filepath, "r") as f:
                data = json.load(f)
            return data.get("state")
        except Exception:
            return None

    def delete_investigation(self, investigation_id: str) -> bool:
        """Delete JSON file."""
        try:
            filepath = self._get_filepath(investigation_id)
            if filepath.exists():
                filepath.unlink()
            return True
        except Exception:
            return False

    def list_investigations(self) -> list:
        """List all investigation IDs from files."""
        try:
            return [f.stem for f in self.directory.glob("*.json")]
        except Exception:
            return []


class StateSerializer:
    """Serializes/deserializes ORACLE investigation state."""

    @staticmethod
    def serialize(investigation: "OracleInvestigation") -> Dict[str, Any]:
        """Convert investigation to serializable dict."""
        from oracle.engine import OracleInvestigation
        
        return {
            "id": investigation.id,
            "question": investigation.question,
            "state": investigation.state.value,
            "max_steps": investigation.max_steps,
            "steps_taken": investigation.steps_taken,
            "created_at": investigation.created_at.isoformat(),
            "primary_hypothesis_id": investigation.primary_hypothesis_id,
            "hypotheses": StateSerializer._serialize_hypotheses(investigation.hypotheses),
            "observations": StateSerializer._serialize_observations(investigation.observations_made),
            "evidence": StateSerializer._serialize_evidence(investigation.evidence_store.get_all_evidence()),
            "plan_history": investigation.plan_history,
        }

    @staticmethod
    def _serialize_hypotheses(hypotheses: Dict) -> Dict:
        """Serialize hypotheses."""
        result = {}
        for hyp_id, hyp in hypotheses.items():
            result[hyp_id] = {
                "id": hyp.id,
                "statement": hyp.statement,
                "created_at": hyp.created_at.isoformat(),
                "confidence_score": hyp.confidence_score,
                "is_primary": hyp.is_primary,
                "rationale": hyp.rationale,
                "supporting_evidence_count": len(hyp.supporting_evidence),
                "contradicting_evidence_count": len(hyp.contradicting_evidence),
            }
        return result

    @staticmethod
    def _serialize_observations(observations: list) -> list:
        """Serialize observations."""
        result = []
        for obs in observations:
            result.append({
                "source": obs.source.value,
                "timestamp": obs.timestamp.isoformat(),
                "raw_data": obs.raw_data,
                "interpretation": obs.interpretation,
                "confidence": obs.confidence.value,
                "metadata": obs.metadata,
            })
        return result

    @staticmethod
    def _serialize_evidence(evidence_list: list) -> list:
        """Serialize evidence."""
        result = []
        for evidence in evidence_list:
            result.append({
                "observation_source": evidence.observation.source.value,
                "observation_timestamp": evidence.observation.timestamp.isoformat(),
                "supports_hypotheses": evidence.supports_hypotheses,
                "contradicts_hypotheses": evidence.contradicts_hypotheses,
                "supporting_strength": evidence.supporting_strength,
                "contradicting_strength": evidence.contradicting_strength,
                "analysis": evidence.analysis,
                "created_at": evidence.created_at.isoformat(),
            })
        return result

    @staticmethod
    def get_summary(serialized: Dict[str, Any]) -> Dict[str, Any]:
        """Extract summary from serialized state."""
        return {
            "id": serialized["id"],
            "question": serialized["question"],
            "state": serialized["state"],
            "steps_taken": serialized["steps_taken"],
            "max_steps": serialized["max_steps"],
            "primary_hypothesis": serialized.get("primary_hypothesis_id"),
            "hypotheses_count": len(serialized["hypotheses"]),
            "observations_count": len(serialized["observations"]),
            "evidence_count": len(serialized["evidence"]),
            "created_at": serialized["created_at"],
        }
