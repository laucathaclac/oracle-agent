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
        pass

    @abstractmethod
    def load_investigation(self, investigation_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_investigation(self, investigation_id: str) -> bool:
        pass

    @abstractmethod
    def list_investigations(self) -> list:
        pass


class InMemoryPersistence(PersistenceBackend):
    """In-memory persistence backend for tests and ephemeral agents."""

    def __init__(self):
        self.store: Dict[str, Dict[str, Any]] = {}
        self.access_log: list = []

    def save_investigation(self, investigation_id: str, state: Dict[str, Any]) -> bool:
        try:
            snapshot = json.loads(json.dumps(state, default=str))
            self.store[investigation_id] = {
                "state": snapshot,
                "saved_at": datetime.utcnow().isoformat(),
            }
            self.access_log.append({"action": "save", "id": investigation_id, "timestamp": datetime.utcnow()})
            return True
        except Exception as exc:
            self.access_log.append({"action": "save_error", "id": investigation_id, "error": str(exc)})
            return False

    def load_investigation(self, investigation_id: str) -> Optional[Dict[str, Any]]:
        self.access_log.append({"action": "load", "id": investigation_id, "timestamp": datetime.utcnow()})
        entry = self.store.get(investigation_id)
        return entry["state"] if entry else None

    def delete_investigation(self, investigation_id: str) -> bool:
        self.store.pop(investigation_id, None)
        self.access_log.append({"action": "delete", "id": investigation_id, "timestamp": datetime.utcnow()})
        return True

    def list_investigations(self) -> list:
        return list(self.store.keys())

    def clear(self) -> None:
        self.store.clear()


class FilePersistence(PersistenceBackend):
    """File-based JSON persistence backend."""

    def __init__(self, directory: str = ".oracle_state"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _get_filepath(self, investigation_id: str) -> Path:
        return self.directory / f"{investigation_id}.json"

    def save_investigation(self, investigation_id: str, state: Dict[str, Any]) -> bool:
        try:
            filepath = self._get_filepath(investigation_id)
            payload = {"id": investigation_id, "state": state, "saved_at": datetime.utcnow().isoformat()}
            with open(filepath, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, default=str, indent=2)
            return True
        except Exception:
            return False

    def load_investigation(self, investigation_id: str) -> Optional[Dict[str, Any]]:
        try:
            filepath = self._get_filepath(investigation_id)
            if not filepath.exists():
                return None
            with open(filepath, "r", encoding="utf-8") as handle:
                return json.load(handle).get("state")
        except Exception:
            return None

    def delete_investigation(self, investigation_id: str) -> bool:
        try:
            filepath = self._get_filepath(investigation_id)
            if filepath.exists():
                filepath.unlink()
            return True
        except Exception:
            return False

    def list_investigations(self) -> list:
        try:
            return [path.stem for path in self.directory.glob("*.json")]
        except Exception:
            return []


class StateSerializer:
    """Serialize ORACLE state into JSON-compatible dictionaries."""

    @staticmethod
    def serialize(investigation: "OracleInvestigation") -> Dict[str, Any]:
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
        return {
            hyp_id: {
                "id": hyp.id,
                "statement": hyp.statement,
                "created_at": hyp.created_at.isoformat(),
                "confidence_score": hyp.confidence_score,
                "is_primary": hyp.is_primary,
                "rationale": hyp.rationale,
                "supporting_evidence_count": len(hyp.supporting_evidence),
                "contradicting_evidence_count": len(hyp.contradicting_evidence),
            }
            for hyp_id, hyp in hypotheses.items()
        }

    @staticmethod
    def _serialize_observations(observations: list) -> list:
        return [
            {
                "source": obs.source.value,
                "timestamp": obs.timestamp.isoformat(),
                "raw_data": obs.raw_data,
                "interpretation": obs.interpretation,
                "confidence": obs.confidence.value,
                "metadata": obs.metadata,
            }
            for obs in observations
        ]

    @staticmethod
    def _serialize_evidence(evidence_list: list) -> list:
        return [
            {
                "observation_source": evidence.observation.source.value,
                "observation_timestamp": evidence.observation.timestamp.isoformat(),
                "supports_hypotheses": evidence.supports_hypotheses,
                "contradicts_hypotheses": evidence.contradicts_hypotheses,
                "supporting_strength": evidence.supporting_strength,
                "contradicting_strength": evidence.contradicting_strength,
                "analysis": evidence.analysis,
                "created_at": evidence.created_at.isoformat(),
            }
            for evidence in evidence_list
        ]

    @staticmethod
    def get_summary(serialized: Dict[str, Any]) -> Dict[str, Any]:
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
