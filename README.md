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

The first prototype is intentionally small and dependency-free. It includes:

- `ExpertModule`: metadata and a callable mock module.
- `ModuleRegistry`: a simple registry for available modules.
- `Router`: keyword/domain matching over task text.
- `RoutingDecision`: selected modules, skipped modules, scores, and reasons.
- A demo showing that different tasks activate different modules.

This is not a production router, not a trained model, and not a complete agent framework. It is a readable starting point for exploring sparse modular AI behavior.

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

## Run the Demo

From the repository root:

```bash
python examples/basic_routing_demo.py
```

The example runs several tasks through the router: code assistance, car diagnostics, cybersecurity, media/video workflow, and document search. For each task it prints selected modules, reasons, scores, skipped modules, and mock outputs from the activated modules.

## Current Limitations

- Routing is simple keyword/domain matching.
- Experts are mock modules, not real tools or models.
- There is no database, vector store, web server, or UI yet.
- Feedback is described in the architecture but not implemented yet.

These limits are intentional. The project starts as a clear research prototype before adding heavier infrastructure.
