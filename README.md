# Grona

Grona is a research/prototype project for a modular sparse AI architecture inspired by the structure of a grape cluster.

The project explores a simple question: what if an AI system did not activate its whole "brain" for every task? Instead of routing every request through one monolithic model or one dense execution path, Grona routes a task to only the modules that appear relevant: expert modules, memory modules, tools, local models, databases, search indexes, or APIs.

## The Grape-Cluster Metaphor

The grape cluster is a practical architecture metaphor:

- The vine or stem is the coordination layer.
- Branches are high-level domains or task families.
- Grapes are specialized modules that can be activated independently.
- New grapes can be attached without rebuilding the whole cluster.
- Bad, outdated, or expensive grapes can be replaced without retraining everything.

The metaphor matters because it pushes the design away from a single all-purpose component. Grona should grow as a cluster of replaceable parts, with routing logic deciding which parts should wake up for a specific task.

## Why Not a Monolithic AI Model?

Many AI systems behave like monolithic brains: a single large model receives the whole task, all available context, and every tool description. That can work, but it often wastes compute, hides decisions, and makes it hard to replace one weak capability without disturbing the rest of the system.

Grona explores the opposite direction:

1. Route first, think second.
2. Activate only relevant modules.
3. Keep routing decisions explainable.
4. Let modules have their own scope, cost, and memory.
5. Make modules easy to add, remove, or replace.

## Relationship to MoE and Sparse Activation

Grona is related to Mixture of Experts, sparse activation, routing networks, modular agents, retrieval-augmented generation, tool-using AI, and local AI orchestration. It should not be described as just another MoE system.

Classic MoE usually refers to learned expert layers inside a neural network. Grona is broader: an expert can be a local LLM, a script, a database query layer, a vector index, a code analyzer, a cybersecurity scanner, a media tool, a domain-specific memory module, or an API wrapper.

The shared idea is sparsity. The broader Grona idea is heterogeneous modular activation across models, tools, memory, and orchestration.

## First Prototype

The first prototype is intentionally small and dependency-free at runtime. It includes:

- `ExpertModule`: metadata and a callable mock module.
- `ModuleRegistry`: a simple registry for available modules.
- `Router`: keyword/domain matching over task text.
- `RoutingDecision`: selected modules, skipped modules, scores, and reasons.
- A default demo registry for code, car diagnostics, cybersecurity, media/video, document search, and general reasoning.
- A CLI and tests so the project is easier to run and extend.

This is not a production router, not a trained model, and not a complete agent framework. It is a readable starting point for exploring sparse modular AI behavior.

## Install From the Repository

```bash
pip install -e .
```

For development tools:

```bash
pip install -e .[dev]
```

## Run the Demo

```bash
python examples/basic_routing_demo.py
```

Or use the console script installed by the package:

```bash
grona-demo "Analyze engine overheating symptoms"
```

You can also run the package as a module:

```bash
python -m grona "Review firewall logs for suspicious port scans"
```

The demo prints selected modules, skipped modules, reasons, scores, and mock outputs from activated modules.

## Run Tests

```bash
pytest
```

Optional linting:

```bash
ruff check .
```

## Repository Layout

```text
.
├── .github/workflows/tests.yml
├── docs/
│   ├── architecture.md
│   ├── development.md
│   ├── research-notes.md
│   └── roadmap.md
├── examples/
│   └── basic_routing_demo.py
├── src/
│   └── grona/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── decision.py
│       ├── defaults.py
│       ├── module.py
│       ├── registry.py
│       └── router.py
├── tests/
├── pyproject.toml
└── README.md
```

## Development Philosophy

- Keep routing decisions visible.
- Keep modules small, replaceable, and metadata-driven.
- Prefer local-first building blocks where possible.
- Add heavier infrastructure only after the simple prototype proves what it needs.
- Treat tests as a guardrail for explainable behavior, not as a claim that routing is solved.

## Current Limitations

- The router is keyword-based.
- There is no real LLM integration yet.
- There is no learning or adaptive routing yet.
- There is no memory graph yet.
- There is no vector database or retrieval engine yet.
- There is no production orchestration yet.
- Expert modules are mock/demo modules, not real AI tools.

These limits are intentional. Grona is currently a research/prototype foundation for sparse modular AI architecture.
