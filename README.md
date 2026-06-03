# Grona

Grona is a lightweight research prototype for a modular sparse AI architecture inspired by grape-cluster-like expert activation.

The core idea is simple: do not activate every capability for every task. Route a task to a small relevant set of expert modules, build only route-scoped context, prepare a structured handoff, and keep the decision trace visible.

## Architecture Metaphor

- The vine or stem is the coordination layer.
- Branches are high-level domains or task families.
- Grapes are specialized modules that can be activated independently.
- New grapes can be attached without rebuilding the whole cluster.
- Weak or expensive grapes can be replaced without disturbing the whole system.

In the current prototype, the router chooses relevant branches and grapes, the context builder gathers only the information needed by those selected grapes, the orchestrator coordinates the selected path, and the feedback layer remembers which paths worked.

## Current Prototype

The current prototype includes:

- `ExpertModule`: metadata and a callable mock expert for routing demos.
- `ModuleRegistry`: a simple catalog of available modules.
- `Router`: keyword/domain/capability routing.
- `RoutingDecision`: selected/skipped modules, scores, reasons, and feedback metadata.
- `FeedbackRecord`: route history records with optional rating and success/failure outcome.
- `InMemoryFeedbackStore` and `JsonlFeedbackStore`: simple route history stores.
- `AdaptiveRoutingConfig`: opt-in feedback-informed score adjustments.
- `ContextItem` and `ContextBuilder`: route-scoped synthetic context for selected modules.
- `Orchestrator` and `OrchestrationResult`: visible routing, context building, and planned handoff.
- CLI, examples, tests, and GitHub Actions CI.

The default demo registry includes modules for code, car diagnostics, cybersecurity, media/video, document search, and general reasoning.

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
```

Or use the console script:

```bash
grona-demo "Analyze engine overheating symptoms"
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

Build route-scoped context and prepare an orchestration handoff:

```bash
python -m grona "Review this Python script for security issues" --orchestrate
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
|   |-- architecture.md
|   |-- development.md
|   |-- orchestration.md
|   |-- research-notes.md
|   `-- roadmap.md
|-- examples/
|   |-- adaptive_routing_demo.py
|   |-- basic_routing_demo.py
|   |-- feedback_demo.py
|   `-- orchestration_demo.py
|-- src/grona/
|   |-- __init__.py
|   |-- __main__.py
|   |-- adaptive.py
|   |-- cli.py
|   |-- context.py
|   |-- decision.py
|   |-- defaults.py
|   |-- feedback.py
|   |-- module.py
|   |-- orchestrator.py
|   |-- registry.py
|   `-- router.py
|-- tests/
|-- pyproject.toml
`-- README.md
```

## Development Philosophy

- Keep routing decisions visible.
- Keep modules small, replaceable, and metadata-driven.
- Keep context route-scoped instead of loading everything for every task.
- Keep orchestration honest: planned handoff now, execution later.
- Keep adaptive routing opt-in, bounded, deterministic, and explainable.
- Add heavier infrastructure only after the simple prototype proves what it needs.
- Treat tests as a guardrail for explainable behavior, not as proof that routing is solved.

## Current Limitations

- The router is keyword-based.
- Context building is synthetic demo context, not retrieval.
- The orchestrator prepares a structured handoff but does not execute real experts yet.
- Adaptive routing is deterministic score adjustment, not machine learning.
- There is no real LLM integration yet.
- There is no neural learning yet.
- There is no memory graph yet.
- There is no vector database or retrieval engine yet.
- There is no web server.
- There is no production orchestration.
- Expert modules are mock/demo modules, not real AI tools.

These limits are intentional. Grona is currently a research/prototype foundation for sparse modular AI architecture.
