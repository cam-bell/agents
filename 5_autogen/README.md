# Self-Replicating Agent System (AutoGen Core)

This project demonstrates a distributed, self-expanding multi-agent workflow built with AutoGen Core + AgentChat.

## What It Does

`world.py` starts a gRPC runtime, registers a `Creator` agent, and concurrently asks it to generate and run `N` new agents.

For each generated agent:

1. `Creator` uses `agent.py` as a template.
2. It writes new Python code (`agent{i}.py`) with a distinct system prompt.
3. It dynamically imports and registers that new agent in the runtime.
4. It asks the new agent for a startup business idea.
5. The result is saved as `idea{i}.md`.

Generated agents can optionally bounce ideas to other generated agents for refinement.

## Architecture

- `world.py`: Orchestrator and concurrent runner (`HOW_MANY_AGENTS`).
- `creator.py`: Meta-agent that writes, imports, and registers new agents.
- `agent.py`: Base agent template used for generation.
- `messages.py`: Shared message schema and random recipient selection.

## Run

Prereqs:

- Python 3.10+
- Project dependencies installed (from repo root)
- `OPENAI_API_KEY` available via environment or `.env`

From `5_autogen/`:

```bash
python world.py
```

## Sample Outputs

Curated examples are included in `5_autogen/examples/`:

- `5_autogen/examples/finance-quest-gamified-finance.md`
- `5_autogen/examples/smart-credit-ecosystem.md`
- `5_autogen/examples/ai-real-estate-investment-analyzer.md`

## Notes

- Runtime endpoint is currently `localhost:50051`.
- The model in this setup is `gpt-4o-mini`.
- Generated outputs are non-deterministic because of model randomness and agent-to-agent refinement.
