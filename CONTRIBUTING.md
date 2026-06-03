# Contributing

Thanks for your interest in Grona. This repository is an early research prototype, so contributions should keep the system small, deterministic, inspectable, and honest about its limits.

## Prototype Status

Grona currently contains routing, workspaces, deterministic memory, in-memory document ingestion, orchestration, demo executors, execution adapters, mock tools, and safety planning. It does not contain real LLM integration, real tool execution, shell execution, sandboxing, external APIs, or production deployment.

## Local Development

```bash
pip install -e .[dev]
pytest
ruff check .
```

Run examples:

```bash
python examples/basic_routing_demo.py
python examples/workspace_profile_demo.py
python -m grona "Diagnose engine overheating" --workspace automotive
```

## Useful Contribution Areas

- clearer documentation and examples
- deterministic routing tests
- workspace profile experiments
- memory and context-builder improvements
- safety-policy tests and edge cases
- mock adapter/tool contracts
- benchmark ideas for routing and orchestration
- research notes for Growth Lab, KnowledgeSeed, GrapeCluster, and related concepts

## Dependency Policy

Avoid heavy dependencies unless there is a clear design discussion first. The prototype should stay easy to install, run, and inspect.

Do not add external config frameworks, databases, real LLM clients, vector stores, web servers, or tool execution dependencies without a focused proposal.

## Safety Policy

Execution and tool features must be safety-first. New code should not execute shell commands, spawn subprocesses, read or write arbitrary files, call networks, or claim sandboxing unless the repository explicitly implements and tests those boundaries.

Mock tools should remain deterministic and clearly labeled as mock behavior.

## Documentation Tone

Be direct about limitations. Avoid production claims. Prefer wording that explains what the prototype demonstrates and what it intentionally does not do yet.