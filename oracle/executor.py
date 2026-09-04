"""Tool execution engine for autonomous investigation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from oracle.types import Observation, EvidenceSource, ConfidenceLevel


@dataclass
class ToolResult:
    """Result from tool execution."""
    tool_name: str
    success: bool
    data: Any
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_observation(self, source: EvidenceSource) -> Optional[Observation]:
        """Convert successful result to observation."""
        if not self.success or self.data is None:
            return None
        
        interpretation = self.data.get("interpretation", "") if isinstance(self.data, dict) else str(self.data)
        confidence_str = self.data.get("confidence", "medium") if isinstance(self.data, dict) else "medium"
        
        try:
            confidence = ConfidenceLevel(confidence_str.lower())
        except (ValueError, AttributeError):
            confidence = ConfidenceLevel.MEDIUM
        
        return Observation(
            source=source,
            timestamp=self.timestamp,
            raw_data=self.data,
            interpretation=interpretation,
            confidence=confidence,
            metadata={"tool": self.tool_name}
        )


class Tool(ABC):
    """Base class for investigation tools."""

    def __init__(self, name: str, description: str, tags: List[str] = None):
        self.name = name
        self.description = description
        self.tags = tags or []
        self.execution_count = 0
        self.last_execution: Optional[datetime] = None

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, type]:
        """Return expected parameters and their types."""
        pass

    def get_info(self) -> Dict:
        """Get tool metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "execution_count": self.execution_count,
            "last_execution": self.last_execution,
            "parameters": self.get_parameters(),
        }


class ToolExecutor:
    """Executes tools and handles errors gracefully."""

    def __init__(self, registry: "ToolRegistry"):
        self.registry = registry
        self.execution_history: List[Dict] = []

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name and track execution."""
        tool = self.registry.get_tool(tool_name)
        
        if not tool:
            result = ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                error=f"Tool '{tool_name}' not registered",
                timestamp=datetime.utcnow()
            )
            self.execution_history.append({
                "tool": tool_name,
                "success": False,
                "error": result.error,
                "timestamp": result.timestamp
            })
            return result

        try:
            result = tool.execute(**kwargs)
            tool.execution_count += 1
            tool.last_execution = datetime.utcnow()
            
            self.execution_history.append({
                "tool": tool_name,
                "success": result.success,
                "error": result.error,
                "timestamp": result.timestamp
            })
            
            return result
        except Exception as e:
            result = ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                error=f"Execution error: {str(e)}",
                timestamp=datetime.utcnow()
            )
            self.execution_history.append({
                "tool": tool_name,
                "success": False,
                "error": result.error,
                "timestamp": result.timestamp
            })
            return result

    def get_execution_history(self) -> List[Dict]:
        """Get execution history."""
        return self.execution_history.copy()


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.executor = ToolExecutor(self)

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        if tool.name in self.tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self.tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool."""
        if tool_name in self.tools:
            del self.tools[tool_name]

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(tool_name)

    def get_tools_by_tag(self, tag: str) -> List[Tool]:
        """Get tools by tag."""
        return [tool for tool in self.tools.values() if tag in tool.tags]

    def list_tools(self) -> List[Dict]:
        """List all available tools."""
        return [tool.get_info() for tool in self.tools.values()]

    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        return self.executor.execute(tool_name, **kwargs)

    def get_available_tools(self) -> Dict[str, str]:
        """Get mapping of tool names to descriptions."""
        return {tool.name: tool.description for tool in self.tools.values()}
