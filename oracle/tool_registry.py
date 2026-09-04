"""Tool registry abstraction for pluggable Binance Agent OS MCP tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Result from tool execution."""
    tool_name: str
    success: bool
    data: Any
    error: Optional[str] = None


class BaseTool(ABC):
    """Base class for all tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        pass


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self.tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool."""
        if tool_name in self.tools:
            del self.tools[tool_name]

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.tools.get(tool_name)

    def list_tools(self) -> List[Dict[str, str]]:
        """List all available tools."""
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self.tools.values()
        ]

    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                error=f"Tool '{tool_name}' not found",
            )
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                error=str(e),
            )
