# Context Building and Orchestration

Grona now includes a small context builder and orchestrator layer. This is still a research prototype, not a production agent runtime.

## Context Builder

`ContextBuilder` receives a `RoutingDecision` and creates one `ContextItem` for each selected module.

A `ContextItem` contains:

- `source`: a readable source label such as `demo:automotive-diagnostics`
- `content`: a short route-scoped context string
- `relevance`: a normalized score between `0.0` and `1.0`
- `metadata`: small structured details about the module and score

The current context is synthetic. It does not retrieve from files, databases, vector indexes, web APIs, or LLM memory. The goal is to define the shape of route-scoped context before adding real retrieval systems.

## Orchestrator

`Orchestrator` coordinates three steps:

1. Route the task with `Router`.
2. Build context with `ContextBuilder`.
3. Invoke only the selected demo modules.

It returns an `OrchestrationResult` with:

- original task
- routing decision
- context items
- module outputs
- summary
- small metadata counts

The orchestrator is intentionally sequential and explicit. It does not do retries, parallel execution, dependency planning, tool scheduling, or final answer synthesis yet.

## CLI Usage

```bash
python -m grona "Review this Python script for security issues" --orchestrate
```

This prints:

- selected modules
- skipped modules
- routing reasons and scores
- context items
- selected module outputs
- orchestration summary

## Why This Layer Exists

A sparse modular system should not only select modules. It should also avoid loading every possible source of context for every task.

The context builder is the place where future versions can add route-scoped retrieval from local files, document indexes, structured notes, databases, memory graphs, or APIs. The orchestrator is the place where future versions can execute selected modules in a more deliberate order.

For now, both layers stay lightweight so the route trace remains easy to inspect.

## What Not to Add Yet

Do not add these to this layer yet:

- web servers
- vector databases
- heavy agent frameworks
- external LLM dependencies
- hidden global memory
- production job queues
- opaque planning loops
- automatic retries without tests and trace output

The next useful step is to replace selected synthetic context stubs with simple local, testable context sources.
