# Grona

Grona is a lightweight research prototype for a modular sparse AI architecture inspired by grape-cluster-like expert activation.

The core idea is simple: do not activate every capability for every task. Route a task to a small relevant set of expert modules, gather only focused context from stubs or memory modules, prepare a structured handoff, and keep the decision trace visible.

## Architecture Metaphor

- The router chooses relevant branches and grapes.
- Memory modules are small knowledge pockets attached to parts of the cluster.
- The context builder gathers only the information needed by selected grapes.
- The orchestrator coordinates the selected path.
- The feedback layer remembers which paths worked.
- Adaptive routing slightly adjusts future activation from previous outcomes.

## Current Prototype

The current prototype includes:

- `ExpertModule`: metadata and a callable mock expert for routing demos.
- `ModuleRegistry`: a simple catalog of available modules.
- `Router`: keyword/domain/capability routing.
- `RoutingDecision`: selected/skipped modules, scores, reasons, and feedback metadata.
- `FeedbackRecord`: route history records with optional rating and success/failure outcome.
- `AdaptiveRoutingConfig`: opt-in feedback-informed score adjustments.
- `ContextItem` and `ContextBuilder`: route-scoped context for selected modules.
- `MemoryRecord`, `MemoryModule`, and `InMemoryKeywordMemory`: deterministic memory/retrieval stubs.
- `JsonlMemoryStore`: a tiny JSONL record loader/writer for memory records.
- `Orchestrator` and `OrchestrationResult`: visible routing, context building, and planned handoff.
- CLI, examples, tests, and GitHub Actions CI.

The default demo registry includes modules for code, car diagnostics, cybersecurity, media/video, document search, and general reasoning. The default demo memory contains small records for the same domains.

## Install

```bash
pip install -e .
```

For tests and linting:

```bash
pip install -e .[dev]
```

## Run Demos

```bash
python examples/basic_routing_demo.py
python examples/feedback_demo.py
python examples/adaptive_routing_demo.py
python examples/orchestration_demo.py
python examples/memory_demo.py
```

## Run the CLI

Route a task:

```bash
python -m grona "Review firewall logs for suspicious port scans"
```

Enable adaptive routing from feedback history:

```bash
python -m grona "Analyze engine overheating symptoms" --feedback-file feedback.jsonl --adaptive
```

Build route-scoped context with stubs only:

```bash
python -m grona "Review this Python script for security issues" --orchestrate
```

Build route-scoped context with demo memory:

```bash
python -m grona "Diagnose engine overheating" --orchestrate --use-demo-memory
```

Save route feedback:

```bash
python -m grona "Analyze engine overheating symptoms" --feedback-file feedback.jsonl --rating 5 --success true --notes "Good route"
```

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
|-- .github/workflows/tests.yml
|-- docs/
|-- examples/
|   |-- adaptive_routing_demo.py
|   |-- basic_routing_demo.py
|   |-- feedback_demo.py
|   |-- memory_demo.py
|   `-- orchestration_demo.py
|-- src/grona/
|   |-- adaptive.py
|   |-- cli.py
|   |-- context.py
|   |-- feedback.py
|   |-- memory.py
|   |-- orchestrator.py
|   |-- router.py
|   `-- ...
|-- tests/
|-- pyproject.toml
`-- README.md
```

## Memory Modules

Memory modules are not feedback stores. Feedback stores remember route outcomes. Memory modules provide small knowledge records to the context builder when a route selects relevant domains or capabilities.

Current retrieval is deterministic keyword/domain overlap only. There are no embeddings, semantic search, vector databases, SQL databases, document ingestion pipelines, memory graphs, or external APIs.

Future vector, RAG, local index, or memory graph systems can plug in later by implementing the `MemoryModule` protocol and returning `ContextItem` values.

## Development Philosophy

- Keep routing decisions visible.
- Keep modules small, replaceable, and metadata-driven.
- Keep memory retrieval deterministic until a stronger baseline is needed.
- Keep context route-scoped instead of loading everything for every task.
- Keep orchestration honest: planned handoff now, execution later.
- Keep adaptive routing opt-in, bounded, deterministic, and explainable.
- Add heavier infrastructure only after the simple prototype proves what it needs.

## Current Limitations

- The router is keyword-based.
- Memory retrieval is keyword/domain overlap only.
- There is no semantic search or embeddings yet.
- There is no real document ingestion yet.
- There is no persistent memory graph yet.
- The orchestrator prepares a structured handoff but does not execute real experts yet.
- Adaptive routing is deterministic score adjustment, not machine learning.
- There is no real LLM integration yet.
- There is no vector database, SQL database, web server, or external API integration.
- Expert modules are mock/demo modules, not real AI tools.

These limits are intentional. Grona is currently a research/prototype foundation for sparse modular AI architecture.
