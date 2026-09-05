from oracle.binance_agent_os import (
    BinanceAgentOSTool,
    RemoteToolSpec,
    build_binance_agent_os_registry,
)


class FakeClient:
    def __init__(self):
        self.calls = []

    def list_tools(self):
        return [
            RemoteToolSpec(
                name="get_ticker_price",
                description="Get current market ticker price",
                input_schema={
                    "type": "object",
                    "properties": {"symbol": {"type": "string"}},
                    "required": ["symbol"],
                },
            ),
            RemoteToolSpec(
                name="get_klines",
                description="Get candlestick market data",
                input_schema={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "interval": {"type": "string"},
                    },
                    "required": ["symbol"],
                },
            ),
        ]

    def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return {"interpretation": "BTC market data is constructive", "confidence": "high"}


def test_registry_discovers_read_only_market_tools():
    client = FakeClient()
    registry = build_binance_agent_os_registry(client=client)
    assert "fetch_market_data" in registry.tools
    assert "analyze_technical" in registry.tools


def test_tool_maps_symbol_and_returns_oracle_result():
    client = FakeClient()
    spec = client.list_tools()[0]
    tool = BinanceAgentOSTool(
        "fetch_market_data", spec, client, ["market_data"]
    )

    result = tool.execute(symbol="BTCUSDT")

    assert result.success is True
    assert result.data["confidence"] == "high"
    assert client.calls == [("get_ticker_price", {"symbol": "BTCUSDT"})]


def test_trading_like_tools_are_not_registered():
    class UnsafeClient(FakeClient):
        def list_tools(self):
            return [
                RemoteToolSpec(
                    name="place_order",
                    description="Place a market buy order",
                    input_schema={"type": "object"},
                ),
            ]

    try:
        build_binance_agent_os_registry(client=UnsafeClient())
    except RuntimeError as exc:
        assert "no compatible read-only" in str(exc)
    else:
        raise AssertionError("unsafe tools must not be registered")
