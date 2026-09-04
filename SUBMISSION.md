# Binance Agent OS Mini Hackathon — Track A

## Project

**ORACLE — Autonomous Crypto Research Agent**

## One-line pitch

> ORACLE turns crypto research from one-shot summarization into an auditable investigation: it creates competing hypotheses, chooses the next evidence to gather, executes tools, scores evidence by reliability, attacks its leading conclusion, replans, and reports what would change its mind.

## Problem

Crypto agents can retrieve large amounts of data but often collapse uncertainty into a confident narrative. That makes it difficult to see which evidence mattered, what was ignored, or what would falsify the conclusion.

## Solution

ORACLE introduces an explicit investigation loop:

**Goal → Hypotheses → Plan → Tools → Evidence → Confidence → Critique → Replan → Verdict**

Every stage is represented in code and is independently testable.

## Agent OS fit

ORACLE is designed around a provider-agnostic tool boundary. Binance Agent OS/MCP tools can be exposed through adapters implementing ORACLE's `Tool` contract. The engine does not own credentials or trading permissions; those remain with the Agent OS-compatible client.

For judging, the repository includes a deterministic, keyless demo that exercises the same execution path end-to-end.

## What the demo proves

- Autonomous tool selection from evidence gaps
- Real tool execution through a registry/executor
- Tool output converted into observations
- Evidence linked to competing hypotheses
- Source-aware confidence weighting
- Adversarial critique
- Dynamic replanning
- Persistence checkpoints
- Auditable final verdict

## Novelty

The differentiator is not another crypto chatbot. ORACLE is a **research control loop**. It treats uncertainty and contradiction as first-class state and makes the agent's reasoning process inspectable without exposing hidden chain-of-thought.

## Safety

The repository demo uses synthetic data and requires no funds or credentials. Live Agent OS integrations should use the minimum permissions required and keep credentials outside source control.

## Demo command

```bash
python -m pip install -e '.[dev]'
pytest -q
python demo.py
```

## Repository

`https://github.com/laucathaclac/oracle-agent`

## Suggested 90-second video

**0–10s:** Show the question and three competing hypotheses.

**10–30s:** Show ORACLE selecting missing evidence domains and executing tools.

**30–50s:** Show the evidence ledger and confidence changing as evidence arrives.

**50–70s:** Show the adversarial critic and the next plan changing.

**70–90s:** Show the final verdict: confidence, evidence counts, assumptions, and exactly what would change the conclusion.

## Closing line

> **Don't ask an agent only for an answer. Ask it to investigate whether its own answer deserves to be trusted.**
