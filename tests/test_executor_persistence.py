"""Tests for tool execution infrastructure and state persistence."""

import pytest
import tempfile
from pathlib import Path
from oracle.executor import Tool, ToolResult, ToolRegistry
from oracle.persistence import InMemoryPersistence, FilePersistence, StateSerializer
from oracle.types import EvidenceSource, ConfidenceLevel


class MockTool(Tool):
    """Mock tool for testing."""
    
    def __init__(self, name: str = "mock_tool", fail: bool = False):
        super().__init__(name, f"Mock tool for testing", tags=["test", "mock"])
        self.fail = fail
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute mock tool."""
        if self.fail:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                error="Mock tool failed"
            )
        
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={
                "interpretation": "Mock result",
                "confidence": "high"
            }
        )
    
    def get_parameters(self):
        return {"query": str}


def test_tool_result_to_observation():
    """Test converting ToolResult to Observation."""
    result = ToolResult(
        tool_name="test_tool",
        success=True,
        data={
            "interpretation": "Test interpretation",
            "confidence": "high"
        }
    )
    
    obs = result.to_observation(EvidenceSource.MARKET_DATA)
    
    assert obs is not None
    assert obs.source == EvidenceSource.MARKET_DATA
    assert obs.interpretation == "Test interpretation"
    assert obs.confidence == ConfidenceLevel.HIGH


def test_tool_registry_register():
    """Test registering a tool."""
    registry = ToolRegistry()
    tool = MockTool("test_tool")
    
    registry.register(tool)
    
    assert registry.get_tool("test_tool") is tool


def test_tool_registry_execute_success():
    """Test successful tool execution."""
    registry = ToolRegistry()
    tool = MockTool("test_tool", fail=False)
    registry.register(tool)
    
    result = registry.execute_tool("test_tool")
    
    assert result.success is True
    assert result.tool_name == "test_tool"


def test_tool_registry_execute_failure():
    """Test failed tool execution."""
    registry = ToolRegistry()
    tool = MockTool("test_tool", fail=True)
    registry.register(tool)
    
    result = registry.execute_tool("test_tool")
    
    assert result.success is False
    assert result.error is not None


def test_in_memory_persistence_save_load():
    """Test saving and loading investigation state."""
    backend = InMemoryPersistence()
    state = {
        "id": "inv-123",
        "question": "Test question",
        "state": "ANALYZING",
        "steps_taken": 5
    }
    
    success = backend.save_investigation("inv-123", state)
    
    assert success is True
    loaded = backend.load_investigation("inv-123")
    assert loaded == state


def test_in_memory_persistence_list():
    """Test listing investigations."""
    backend = InMemoryPersistence()
    backend.save_investigation("inv-1", {"id": "inv-1"})
    backend.save_investigation("inv-2", {"id": "inv-2"})
    
    ids = backend.list_investigations()
    
    assert len(ids) == 2
    assert "inv-1" in ids


def test_file_persistence_save_load():
    """Test file-based persistence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = FilePersistence(tmpdir)
        state = {
            "id": "inv-123",
            "question": "Test question",
            "state": "COMPLETED"
        }
        
        success = backend.save_investigation("inv-123", state)
        
        assert success is True
        loaded = backend.load_investigation("inv-123")
        assert loaded == state


def test_file_persistence_creates_file():
    """Test that JSON file is created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = FilePersistence(tmpdir)
        state = {"id": "inv-123"}
        
        backend.save_investigation("inv-123", state)
        
        filepath = Path(tmpdir) / "inv-123.json"
        assert filepath.exists()


def test_state_serializer_basic():
    """Test serializing investigation state."""
    from oracle.engine import OracleInvestigation
    
    investigation = OracleInvestigation("Test question")
    investigation.initialize_hypotheses(["Hypothesis 1"])
    
    serialized = StateSerializer.serialize(investigation)
    
    assert serialized["id"] == investigation.id
    assert serialized["question"] == "Test question"
    assert len(serialized["hypotheses"]) == 1


def test_state_serializer_summary():
    """Test extracting summary from serialized state."""
    from oracle.engine import OracleInvestigation
    
    investigation = OracleInvestigation("Test question")
    investigation.initialize_hypotheses(["Hypothesis 1"])
    
    serialized = StateSerializer.serialize(investigation)
    summary = StateSerializer.get_summary(serialized)
    
    assert summary["question"] == "Test question"
    assert summary["hypotheses_count"] == 1
