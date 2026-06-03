# Architecture

Grona is a modular sparse AI architecture. Its core design goal is to route each task to the smallest useful set of modules instead of activating every model, memory region, tool, and context source for every request.

## System Diagram

```text
User task
   |
   v
Router -> RoutingDecision -> ContextBuilder -> Orchestrator
             ^                    ^              |
             |                    |              v
      Adaptive Routing       Memory Modules   Expert Results
             ^                                   |
             |                                   v
       Feedback Layer                  Structured handoff/result
```

## Components

### ExpertModule

`ExpertModule` is routing metadata: name, domain, capabilities, keywords, cost, and demo handler. It tells the router which grapes exist and when they might be relevant.

### ExecutableExpert

`ExecutableExpert` is the execution contract. It is separate from `ExpertModule` so metadata and execution can evolve independently. An executor receives the task and focused `ContextItem` values, then returns an `ExpertResult`.

The current executors are deterministic demos. They do not call LLMs, external APIs, shell tools, databases, or scanners.

### ExpertResult

`ExpertResult` stores structured output from an executor:

- module name
- task
- summary
- detail bullets
- confidence
- metadata

This gives the orchestrator a consistent shape for future real expert adapters.

### ExpertExecutorRegistry

The executor registry maps routed module names to executors. If a selected module has no executor, the orchestrator records a missing-executor note instead of crashing.

### Router and Adaptive Routing

The router selects relevant modules using deterministic keyword/domain/capability matching. Adaptive routing can slightly adjust scores from feedback history when enabled.

### Memory Modules and ContextBuilder

Memory modules provide small knowledge records. `ContextBuilder` combines built-in stubs with memory-derived context and passes only focused context to the orchestrator.

### Orchestrator

The orchestrator routes the task, builds focused context, optionally executes deterministic demo experts through the registry, and returns an `OrchestrationResult`.

If no executor registry is provided, orchestration keeps the previous handoff-only behavior.

## Request Lifecycle

1. User task enters the system.
2. Router selects relevant modules.
3. Adaptive routing may adjust scores from feedback history.
4. ContextBuilder prepares stub and memory context for selected modules.
5. Orchestrator optionally calls registered `ExecutableExpert` implementations.
6. Expert results are collected into `OrchestrationResult`.
7. Missing executors are reported in metadata and summary.
8. Feedback can later record whether the route worked.

## Grape-Cluster Metaphor

- Router selects the relevant grapes/modules.
- Memory modules provide relevant knowledge.
- ContextBuilder prepares focused context.
- Orchestrator coordinates the selected path.
- Expert executors are the first tiny working grapes that can respond using context.
- Feedback remembers which execution routes worked.

## Future Execution Adapters

Real future experts could wrap:

- local LLMs
- scripts
- shell tools
- retrievers
- media analyzers
- code analyzers
- cybersecurity scanners

Those are future adapters. The current execution interface is only a deterministic proof of contract.
