# Binance Agent OS Mini Hackathon — Track A

## Project

**ORACLE — Autonomous Crypto Research Agent**

## One-line pitch

> ORACLE turns crypto research from one-shot summarization into an auditable investigation: it creates competing hypotheses, chooses the next evidence to gather, executes tools, scores evidence by reliability, attacks its leading conclusion, replans, and reports what would change its mind.

## Problem

Crypto agents can retrieve large amounts of data but often collapse uncertainty into a confident narrative. That makes it difficult to see which evidence mattered, what was ignored, or what would falsify the conclusion.

## Solution

ORACLE introduces an explicit investigation loop:

**Question → Hypotheses → Plan → Tools → Evidence → Confidence → Critique → Replan → Verdict**

Every stage is represented in code and is independently testable.

## Agent OS fit

ORACLE is built around a provider-agnostic tool boundary and now includes an optional adapter for Binance's official Agent OS MCP endpoint. The adapter discovers available MCP tools, filters out execution/account-mutation capabilities, maps compatible read-only market-data tools into ORACLE's `Tool` contract, and then runs the normal investigation engine.

The default demo remains deterministic and keyless, while `binance_demo.py` demonstrates the live Agent OS path when the optional MCP client is installed.

## What the demo proves

- Autonomous tool selection from evidence gaps
- Live-tool discovery through Binance Agent OS MCP
- Read-only market-data tool execution through the same registry/executor
- Tool output converted into observations
- Evidence linked to competing hypotheses
- Source-aware confidence weighting
- Adversarial critique
- Dynamic replanning
- Persistence checkpoints
- Auditable final verdict

## Novelty

The differentiator is not another crypto chatbot. ORACLE is a **research control loop**. It treats uncertainty and contradiction as first-class state and makes the agent's research process inspectable without exposing hidden chain-of-thought.

## Safety

The repository's default demo uses synthetic data and requires no funds or credentials. The live adapter is read-only by design: trading, order, transfer, withdrawal, and account-mutation tools are not registered. Credentials and authorization remain outside source control and under the connected Agent OS client.

## Reproduce the keyless demo

```bash
python -m pip install -e '.[dev]'
pytest -q
python demo.py
```

## Reproduce the live Agent OS path

```bash
python -m pip install -e '.[binance]'
python binance_demo.py
```

The live path connects to Binance's official Agent OS MCP endpoint and discovers the currently exposed tools. Market-data access is designed to work without local API keys; any capability that requires authorization must be authorized through the supported Agent OS/MCP client flow.

## Repository

`https://github.com/laucathaclac/oracle-agent`

## Suggested 90-second video

**0–10s:** Show the question and three competing hypotheses.

**10–25s:** Show ORACLE selecting evidence domains and executing tools.

**25–45s:** Show live Binance Agent OS market-data tools feeding the evidence ledger.

**45–60s:** Show source-aware confidence changing as evidence arrives.

**60–75s:** Show the adversarial critic challenging the leading hypothesis and ORACLE replanning.

**75–90s:** Show the final verdict: confidence, evidence counts, and exactly what would change the conclusion.

## Closing line

> **Don't ask an agent only for an answer. Ask it to investigate whether its own answer deserves to be trusted.**
