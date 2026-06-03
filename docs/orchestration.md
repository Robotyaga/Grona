# Context Building and Orchestration

Grona includes a small context builder and orchestrator layer. This is still a research prototype, not a production agent runtime.

## Context Builder

`ContextBuilder` receives a `RoutingDecision` and the original task text. It creates `ContextItem` values for selected modules only.

A `ContextItem` contains:

- `source`: a readable source label such as `demo:automotive-diagnostics`
- `content`: a short route-scoped context string
- `relevance`: a normalized score between `0.0` and `1.0`
- `metadata`: small structured details about the module, domain, capabilities, and score

The current context is synthetic. It does not retrieve from files, databases, vector indexes, web APIs, or LLM memory. The goal is to define the shape of route-scoped context before adding real retrieval systems.

## Orchestrator

`Orchestrator` coordinates three steps:

1. Route the task with `Router`.
2. Build context with `ContextBuilder`.
3. Return a structured `OrchestrationResult` for the next execution layer.

It returns an `OrchestrationResult` with:

- original task
- routing decision
- context items
- selected modules
- summary
- small metadata counts

It does not invoke real experts yet. The summary is intentionally honest: Grona selected modules, prepared focused context, and would pass that context to a future execution layer.

## CLI Usage

```bash
python -m grona "Review this Python script for security issues" --orchestrate
```

This prints:

- routing summary
- selected modules
- skipped modules
- routing reasons and scores
- context items
- orchestration summary
- an explicit note that execution was not run

## Why This Layer Exists

A sparse modular system should not only select modules. It should also avoid loading every possible source of context for every task.

The router chooses the relevant branches and grapes. The context builder gathers only the information needed by those selected grapes. The orchestrator coordinates the selected path. The feedback layer remembers which paths worked. Adaptive routing can slightly adjust future activation based on previous outcomes.

For now, both layers stay lightweight so the route trace remains easy to inspect.

## What Not to Add Yet

Do not add these to this layer yet:

- web servers
- vector databases
- SQL databases
- heavy agent frameworks
- external LLM dependencies
- hidden global memory
- production job queues
- fake AI execution
- opaque planning loops
- automatic retries without tests and trace output

The next useful step is to replace selected synthetic context stubs with simple local, testable context sources.
