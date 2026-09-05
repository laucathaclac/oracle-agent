# ORACLE — Autonomous Crypto Research Agent

**ORACLE** is an investigation-first crypto research agent designed for Binance Agent OS.

Instead of asking an LLM for a one-shot market opinion, ORACLE runs a closed research loop:

```text
QUESTION
   ↓
HYPOTHESES
   ↓
PLAN → SELECT TOOLS → EXECUTE
   ↓
OBSERVE → EVALUATE EVIDENCE
   ↓
REWEIGHT CONFIDENCE
   ↓
ADVERSARIAL CRITIQUE
   ↓
REPLAN
   ↓
VERDICT + WHAT WOULD CHANGE MY MIND
```

The investigation engine is provider-agnostic. The repository now includes an optional adapter for Binance's official Agent OS MCP endpoint, while keeping the default demo deterministic and keyless.

## Why ORACLE is different

Most crypto agents stop at **retrieve → summarize**. ORACLE treats research as an explicit state machine:

- **Competing hypotheses** instead of a single narrative.
- **Evidence ledger** with supporting and contradicting links.
- **Source-aware confidence**: direct market/on-chain evidence receives more weight than social sentiment or inference.
- **Dynamic planning**: the next tools depend on evidence gaps and available tool metadata.
- **Adversarial critic**: the leading hypothesis is challenged before conclusion.
- **Persistence checkpoints**: investigations can be serialized and resumed by a persistence backend.
- **Auditable verdicts**: confidence, evidence counts, assumptions, and reversal conditions are returned together.

## Quick start — deterministic demo

Requires Python 3.10+.

```bash
python -m pip install -e '.[dev]'
pytest -q
python demo.py
```

The demo uses deterministic synthetic data. **No API keys, network access, or trading funds are required.**

## Live Binance Agent OS mode

Binance's official Agent OS MCP endpoint is:

```text
https://agent.binance.com/mcp/agentic
```

The official Binance documentation says the MCP server can expose market data such as tickers, order books, candlesticks, and funding rates without authentication, while account/trading capabilities are permissioned.

Install the optional MCP client:

```bash
python -m pip install -e '.[binance]'
```

Then run:

```bash
python binance_demo.py
```

The live entrypoint:

1. Connects to the official Binance Agent OS MCP endpoint.
2. Discovers the tools exposed by the server.
3. Selects compatible **read-only** market-data tools by name/description.
4. Maps them into ORACLE's existing `Tool` interface.
5. Runs the normal ORACLE investigation loop.
6. Returns a confidence-rated verdict and reversal condition.

No Binance API key is stored in this repository. If Binance's authorization flow is required for a capability, complete it in the supported MCP client environment and grant only the minimum permissions needed.

### Architecture

```text
                         Binance Agent OS
                                │
                         Official MCP Server
                                │
                    live read-only market tools
                                │
                                ▼
QUESTION → HYPOTHESES → PLAN → EXECUTE
                                │
                                ▼
                       EVIDENCE + WEIGHTS
                                │
                                ▼
                         ADVERSARIAL CRITIC
                                │
                         REPLAN if needed
                                │
                                ▼
                    VERDICT + CONFIDENCE
```

### Code path

| Component | Responsibility |
|---|---|
| `oracle/engine.py` | Autonomous investigation loop |
| `oracle/planner.py` | Evidence-gap-driven tool selection |
| `oracle/executor.py` | Tool registry, execution, errors, history |
| `oracle/binance_agent_os.py` | Optional Binance Agent OS MCP bridge |
| `oracle/evidence_store.py` | Evidence indexing and retrieval |
| `oracle/types.py` | Typed observations, evidence, hypotheses, verdicts |
| `oracle/critic.py` | Adversarial challenge checks |
| `oracle/persistence.py` | In-memory/file state persistence |
| `oracle/demo_tools.py` | Safe deterministic demo tools |
| `demo.py` | Keyless deterministic showcase |
| `binance_demo.py` | Live Binance Agent OS showcase |
| `tests/` | Regression and integration-contract tests |

## Tool contract

All integrations use the same small interface:

```python
class Tool(ABC):
    def execute(self, **kwargs) -> ToolResult: ...
    def get_parameters(self) -> Dict[str, type]: ...
```

The Binance adapter discovers MCP tools and wraps them as ORACLE `Tool` instances. The planner consumes their tags, so the investigation engine does not need to know Binance-specific tool names.

## Safety boundary

The live adapter is intentionally **read-only**:

- Trading tools are not registered.
- Order/cancel/buy/sell tools are blocked.
- Transfer/withdrawal/account mutation tools are blocked.
- The default hackathon demo remains deterministic and cannot place orders.

This keeps the Track A Data Analysis demo focused on research rather than execution.

**Never commit API keys, OAuth tokens, session tokens, or private account data.**

## Confidence model

For each hypothesis, evidence contributes:

```text
weighted evidence = strength × source reliability × observation confidence
confidence = (weighted support + prior) /
             (weighted support + weighted contradiction + 2 × prior)
```

The neutral prior prevents a single observation from producing artificial 0% or 100% certainty. The score is decision confidence, not a guarantee or trading signal.

## Testing

GitHub Actions runs the full suite on Python 3.10, 3.11, 3.12 and 3.13. Tests cover initialization, evidence linking, contradictions, dynamic planning, critique, autonomous execution, persistence, serialization, ranking, confidence weighting, and the Binance adapter contract.

```bash
pytest -q
```

## Hackathon demo story

A strong demo shows one question moving through the full loop:

1. Start with three competing market hypotheses.
2. Let ORACLE identify missing evidence domains.
3. Execute several tools through the same executor.
4. Show evidence being attached to hypotheses.
5. Show confidence changing as higher-quality evidence arrives.
6. Show the critic challenge the leader.
7. Replan around the remaining evidence gap.
8. End with a verdict that explicitly states **what evidence would change the conclusion**.

The point is not that ORACLE predicts price perfectly. The point is that it makes an agent's research process **observable, challengeable, and auditable**.

## Official Binance references

- https://www.binance.com/en-NG/support/announcement/detail/07d45cdd3831498f8a4ff339031a8480
- https://www.binance.com/en/square/post/362885563835358
