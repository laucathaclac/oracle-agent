"""Optional Binance Agent OS / MCP integration for ORACLE."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from oracle.executor import Tool, ToolRegistry, ToolResult


BINANCE_AGENT_OS_MCP_URL = "https://agent.binance.com/mcp/agentic"

_READ_ONLY_BLOCKLIST = (
    "trade", "order", "buy", "sell", "cancel", "transfer", "withdraw",
    "deposit", "account", "balance", "position", "wallet",
)

_DOMAIN_KEYWORDS = {
    "market_data": ("ticker", "price", "market", "quote", "book", "depth", "candlestick", "kline", "funding"),
    "technical_analysis": ("kline", "candle", "technical", "indicator", "trend", "momentum"),
    "on_chain": ("onchain", "on-chain", "block", "network", "chain"),
    "social_sentiment": ("sentiment", "social", "fear", "greed"),
}


@dataclass(frozen=True)
class RemoteToolSpec:
    """Minimal MCP tool metadata needed by the ORACLE adapter."""

    name: str
    description: str
    input_schema: Dict[str, Any]


class BinanceAgentOSClient:
    """Synchronous facade over the official Python MCP client."""

    def __init__(self, url: str = BINANCE_AGENT_OS_MCP_URL):
        self.url = url

    @staticmethod
    def _run(coro: Any) -> Any:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        raise RuntimeError(
            "BinanceAgentOSClient is synchronous. Call it outside an active "
            "asyncio event loop or wrap ORACLE in a worker thread."
        )

    async def _list_tools_async(self) -> List[RemoteToolSpec]:
        try:
            from mcp import ClientSession
            from mcp.client.streamable_http import streamable_http_client
        except ImportError as exc:
            raise RuntimeError(
                "Live Binance Agent OS support requires the optional 'binance' "
                "extra: pip install -e '.[binance]'."
            ) from exc

        async with streamable_http_client(self.url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                response = await session.list_tools()
                return [
                    RemoteToolSpec(
                        name=tool.name,
                        description=tool.description or "",
                        input_schema=dict(tool.inputSchema or {}),
                    )
                    for tool in response.tools
                ]

    def list_tools(self) -> List[RemoteToolSpec]:
        return self._run(self._list_tools_async())

    async def _call_tool_async(self, name: str, arguments: Dict[str, Any]) -> Any:
        try:
            from mcp import ClientSession
            from mcp.client.streamable_http import streamable_http_client
        except ImportError as exc:
            raise RuntimeError(
                "Live Binance Agent OS support requires the optional 'binance' extra."
            ) from exc

        async with streamable_http_client(self.url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                return await session.call_tool(name, arguments=arguments)

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        return self._run(self._call_tool_async(name, arguments))


class BinanceAgentOSTool(Tool):
    """Expose one discovered Binance MCP tool through ORACLE's Tool contract."""

    def __init__(
        self,
        alias: str,
        spec: RemoteToolSpec,
        client: BinanceAgentOSClient,
        tags: List[str],
        default_symbol: str = "BTCUSDT",
    ):
        super().__init__(alias, spec.description or spec.name, tags=tags + ["binance", "agent_os", "read_only"])
        self.remote_name = spec.name
        self.input_schema = spec.input_schema
        self.client = client
        self.default_symbol = default_symbol

    def get_parameters(self) -> Dict[str, type]:
        properties = self.input_schema.get("properties", {}) if isinstance(self.input_schema, dict) else {}
        return {name: _python_type(schema) for name, schema in properties.items()}

    def execute(self, **kwargs) -> ToolResult:
        try:
            arguments = _build_arguments(self.input_schema, kwargs, self.default_symbol)
            result = self.client.call_tool(self.remote_name, arguments)
            data = _normalize_mcp_result(result)
            if isinstance(data, dict):
                interpretation = data.get("interpretation") or data.get("summary") or json.dumps(data, default=str)
                data = dict(data)
                data.setdefault("interpretation", interpretation)
                data.setdefault("confidence", "high")
                data["mcp_tool"] = self.remote_name
            else:
                data = {
                    "interpretation": str(data),
                    "confidence": "high",
                    "mcp_tool": self.remote_name,
                    "raw": data,
                }
            return ToolResult(tool_name=self.name, success=True, data=data)
        except Exception as exc:
            return ToolResult(tool_name=self.name, success=False, data=None, error=str(exc))


def _python_type(schema: Dict[str, Any]) -> type:
    kind = schema.get("type") if isinstance(schema, dict) else None
    return {"integer": int, "number": float, "boolean": bool, "array": list, "object": dict}.get(kind, str)


def _build_arguments(schema: Dict[str, Any], kwargs: Dict[str, Any], default_symbol: str = "BTCUSDT") -> Dict[str, Any]:
    """Build conservative arguments for common Binance market-data schemas."""
    properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
    required = schema.get("required", []) if isinstance(schema, dict) else []
    output: Dict[str, Any] = {}
    symbol = kwargs.get("symbol") or kwargs.get("asset") or default_symbol

    for name, definition in properties.items():
        if name in kwargs and kwargs[name] is not None:
            output[name] = kwargs[name]
            continue
        key = name.lower()
        if "symbol" in key:
            output[name] = [symbol] if definition.get("type") == "array" else symbol
        elif key in {"interval", "timeframe", "period"}:
            output[name] = "1h"
        elif key in {"limit", "count", "size"}:
            output[name] = 100
        elif name in required:
            raise ValueError(f"MCP tool requires unsupported argument '{name}'")

    return output


def _normalize_mcp_result(result: Any) -> Any:
    if getattr(result, "isError", False):
        raise RuntimeError(_extract_text(result) or "Binance MCP tool returned an error")
    structured = getattr(result, "structuredContent", None)
    if structured:
        return structured
    text = _extract_text(result)
    if text:
        try:
            return json.loads(text)
        except (TypeError, json.JSONDecodeError):
            return text
    return result


def _extract_text(result: Any) -> str:
    chunks: List[str] = []
    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if text:
            chunks.append(str(text))
    return "\n".join(chunks)


def _score_tool(spec: RemoteToolSpec, domain: str) -> int:
    text = f"{spec.name} {spec.description}".lower()
    return sum(1 for keyword in _DOMAIN_KEYWORDS[domain] if keyword in text)


def _is_read_only_market_tool(spec: RemoteToolSpec) -> bool:
    text = f"{spec.name} {spec.description}".lower()
    return not any(blocked in text for blocked in _READ_ONLY_BLOCKLIST)


def _select_best(specs: Iterable[RemoteToolSpec], domain: str) -> Optional[RemoteToolSpec]:
    candidates = [spec for spec in specs if _is_read_only_market_tool(spec)]
    ranked = sorted(candidates, key=lambda spec: _score_tool(spec, domain), reverse=True)
    if not ranked or _score_tool(ranked[0], domain) == 0:
        return None
    return ranked[0]


def build_binance_agent_os_registry(
    client: Optional[BinanceAgentOSClient] = None,
    include_optional_domains: bool = False,
    symbol: str = "BTCUSDT",
) -> ToolRegistry:
    """Discover Binance MCP tools and expose ORACLE's standard evidence domains."""
    client = client or BinanceAgentOSClient()
    specs = client.list_tools()
    registry = ToolRegistry()

    domains = ["market_data", "technical_analysis"]
    if include_optional_domains:
        domains.extend(["on_chain", "social_sentiment"])

    for domain in domains:
        spec = _select_best(specs, domain)
        if spec is None:
            continue
        alias = {
            "market_data": "fetch_market_data",
            "technical_analysis": "analyze_technical",
            "on_chain": "fetch_on_chain_metrics",
            "social_sentiment": "fetch_social_sentiment",
        }[domain]
        registry.register(BinanceAgentOSTool(alias, spec, client, [domain], default_symbol=symbol))

    if not registry.tools:
        raise RuntimeError(
            "Binance Agent OS MCP returned no compatible read-only market-data tools. "
            "Run the discovery example to inspect the server's current tool list."
        )
    return registry
