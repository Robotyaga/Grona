# Grona

Grona is an early-stage research project for a modular sparse AI architecture inspired by grape-cluster-like expert activation.

The core idea is to organize many small experts into flexible clusters. For each input, a lightweight router activates only the most relevant experts, allowing the system to spend computation where it is useful while keeping inactive capacity available for other contexts.

## Goals

- Explore sparse expert activation as a clean, modular architecture.
- Keep the first implementation small, readable, and easy to extend.
- Separate routing, expert interfaces, experiments, and research notes.
- Build toward reproducible demos before adding heavy training infrastructure.

## Repository Layout

```text
.
├── docs/
│   ├── architecture.md
│   ├── research-notes.md
│   └── roadmap.md
├── examples/
│   └── basic_routing_demo.py
├── src/
│   └── grona/
│       ├── __init__.py
│       └── router.py
├── .gitignore
└── README.md
```

## Quick Demo

Run the lightweight routing demo from the repository root:

```bash
python examples/basic_routing_demo.py
```

The demo creates a few toy experts, scores them against an input vector, and activates the top matching experts.

## Status

This repository is being initialized. The current code is intentionally small and dependency-free so the project can evolve through focused experiments.
