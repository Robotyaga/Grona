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
             ^                                   ^
             |                                   |
       Feedback Layer          Executors or Execution Adapters
```

## Components

### ExpertModule

`ExpertModule` is routing metadata: name, domain, capabilities, keywords, cost, and demo handler. It tells the router which grapes exist and when they might be relevant.

### ExecutableExpert

`ExecutableExpert` is the direct execution contract. It is separate from `ExpertModule` so metadata and execution can evolve independently. An executor receives the task and focused `ContextItem` values, then returns an `ExpertResult`.

The current executors are deterministic demos. They do not call LLMs, external APIs, shell tools, databases, or scanners.

### ExecutionRequest and ExecutionAdapter

`ExecutionRequest` normalizes the task, selected module name, route-scoped context, and metadata passed to an adapter.

`ExecutionAdapter` is a bridge between a selected expert module and a concrete execution backend. It is intentionally separate from both `ExpertModule` metadata and direct `ExecutableExpert` classes.

Future adapters could wrap local Python functions, scripts, shell tools, local LLM wrappers, code analyzers, document processors, media analyzers, or cybersecurity scanners. The current adapters are deterministic and safe only.

### ExpertResult

`ExpertResult` stores structured output from an executor or adapter:

- module name
- task
- summary
- detail bullets
- confidence
- metadata, including backend information when available

This gives the orchestrator a consistent shape for future real expert adapters.

### Registries

`ExpertExecutorRegistry` maps routed module names to direct executors.

`ExecutionAdapterRegistry` maps routed module names to adapters. If a selected module has no adapter, the orchestrator records a missing-adapter note instead of crashing.

When both registries are provided, explicit direct executors take precedence over adapters. This keeps existing behavior predictable while adapters evolve.

### Router and Adaptive Routing

The router selects relevant modules using deterministic keyword/domain/capability matching. Adaptive routing can slightly adjust scores from feedback history when enabled.

### Memory Modules and ContextBuilder

Memory modules provide small knowledge records. `ContextBuilder` combines built-in stubs with memory-derived context and passes only focused context to the orchestrator.

### Orchestrator

The orchestrator routes the task, builds focused context, optionally executes selected modules through direct executors or adapters, and returns an `OrchestrationResult`.

If no execution registry is provided, orchestration keeps the previous handoff-only behavior.

## Request Lifecycle

1. User task enters the system.
2. Router selects relevant modules.
3. Adaptive routing may adjust scores from feedback history.
4. ContextBuilder prepares stub and memory context for selected modules.
5. Orchestrator prefers `ExpertExecutorRegistry` when provided.
6. Otherwise, Orchestrator can use `ExecutionAdapterRegistry` when provided.
7. Expert results are collected into `OrchestrationResult`.
8. Missing executors or adapters are reported in metadata and summary.
9. Feedback can later record whether the route worked.

## Grape-Cluster Metaphor

- Router selects the relevant grapes/modules.
- Memory modules provide relevant knowledge.
- ContextBuilder prepares focused context.
- Expert executors are tiny working grapes that can respond directly.
- Execution adapters are stems from grapes to future execution backends.
- Orchestrator coordinates the selected path and backend choice.
- Feedback remembers which execution routes worked.

## Future Execution Backends

Future adapters may support:

- local Python functions
- local scripts
- shell tools
- local LLM wrappers
- code analyzers
- document processors
- media analyzers
- cybersecurity scanners

These are future backends. Grona does not implement subprocess execution, sandboxing, real tool calls, external APIs, or LLM integration yet.
