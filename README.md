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

The core is provider-agnostic: tools implement a small interface, so Binance Agent OS/MCP tools can be plugged into the same executor without changing the investigation engine.

## Why ORACLE is different

Most crypto agents stop at **retrieve → summarize**. ORACLE treats research as an explicit state machine:

- **Competing hypotheses** instead of a single narrative.
- **Evidence ledger** with supporting and contradicting links.
- **Source-aware confidence**: direct market/on-chain evidence receives more weight than social sentiment or inference.
- **Dynamic planning**: the next tools depend on evidence gaps and hypothesis confidence.
- **Adversarial critic**: the leading hypothesis is challenged before conclusion.
- **Persistence checkpoints**: investigations can be serialized and resumed by a persistence backend.
- **Auditable verdicts**: confidence, evidence counts, assumptions, and reversal conditions are returned together.

## Quick start

Requires Python 3.10+.

```bash
python -m pip install -e '.[dev]'
pytest -q
python demo.py
```

The demo uses deterministic synthetic data. **No API keys or trading funds are required.**

Example output:

```text
=== ORACLE VERDICT ===
Question:    Is BTC market structure bullish?
Conclusion:  BTC market structure is bullish
Confidence:  ...
Evidence:    +... / -...
Tools:       ...
Critiques:   ...
Checkpoints: [...]
Reversal:    Multiple independent sources contradicting the primary hypothesis...
```

## Architecture

| Component | Responsibility |
|---|---|
| `oracle/engine.py` | Autonomous investigation loop |
| `oracle/planner.py` | Evidence-gap-driven tool selection |
| `oracle/executor.py` | Tool registry, execution, errors, history |
| `oracle/evidence_store.py` | Evidence indexing and retrieval |
| `oracle/types.py` | Typed observations, evidence, hypotheses, verdicts |
| `oracle/critic.py` | Adversarial challenge checks |
| `oracle/persistence.py` | In-memory/file state persistence |
| `oracle/demo_tools.py` | Safe deterministic demo tools |
| `demo.py` | End-to-end showcase |
| `tests/` | Regression and subsystem tests |

## Tool contract

A live Agent OS/MCP integration only needs to satisfy the existing `Tool` contract:

```python
class Tool(ABC):
    def execute(self, **kwargs) -> ToolResult: ...
    def get_parameters(self) -> Dict[str, type]: ...
```

Successful `ToolResult` objects become `Observation` objects automatically. ORACLE then evaluates them against the competing hypotheses.

This separation keeps credentials, permissions, and transport outside the research engine.

## Binance Agent OS

Binance Agent OS provides agent access to supported Binance capabilities through user-controlled permissions. The official Binance MCP server currently exposes market-data and trading capabilities; other Agent OS capabilities can be connected through additional Binance APIs, tools, and skills.

For a live integration, connect the chosen MCP-compatible client to Binance's official Agent OS MCP endpoint and map its returned tools to ORACLE's `Tool` interface. Keep the demo path keyless and deterministic for reproducible judging.

Official references:

- https://www.binance.com/en/blog/ecosystem/5991233187660196794
- https://www.binance.com/en-NG/support/announcement/detail/07d45cdd3831498f8a4ff339031a8480

**Never commit API keys, session tokens, or private account data.** Use the minimum permissions required by the live client.

## Confidence model

For each hypothesis, evidence contributes:

```text
weighted evidence = strength × source reliability × observation confidence
confidence = weighted support / (weighted support + weighted contradiction)
```

This is intentionally transparent rather than pretending to be a calibrated probability model. The final verdict reports the score as decision confidence, not a guarantee.

## Testing

GitHub Actions runs the full suite on Python 3.10, 3.11, 3.12 and 3.13. The repository includes tests for initialization, evidence linking, contradictions, dynamic planning, critique, autonomous execution, persistence, serialization, ranking, and confidence weighting.

## Hackathon demo story

A strong demo should show one question moving through the full loop:

1. Start with three competing market hypotheses.
2. Let ORACLE identify missing evidence domains.
3. Execute several tools through the same executor.
4. Show evidence being attached to hypotheses.
5. Show confidence changing as higher-quality evidence arrives.
6. Show the critic challenge the leader.
7. Replan around the remaining evidence gap.
8. End with a verdict that explicitly states **what evidence would change the conclusion**.

The point is not that ORACLE predicts price perfectly. The point is that it makes an agent's research process **observable, challengeable, and auditable**.
