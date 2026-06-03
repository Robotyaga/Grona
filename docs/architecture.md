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
       Feedback Layer        Executors, Adapters, Safety Policy
```

## Components

### ExpertModule

`ExpertModule` is routing metadata: name, domain, capabilities, keywords, cost, and demo handler. It tells the router which grapes exist and when they might be relevant.

### ExecutableExpert

`ExecutableExpert` is the direct execution contract. It is separate from `ExpertModule` so metadata and execution can evolve independently. The current executors are deterministic demos.

### ExecutionRequest and ExecutionAdapter

`ExecutionRequest` normalizes the task, selected module name, route-scoped context, and metadata passed to an adapter.

`ExecutionAdapter` is a bridge between a selected expert module and a concrete execution backend. Future adapters could wrap local Python functions, scripts, shell tools, local LLM wrappers, code analyzers, document processors, media analyzers, or cybersecurity scanners. The current adapters are deterministic and safe only.

### Safety Policy Layer

The safety layer evaluates planned actions before any future adapter can run a real tool.

- `ToolAction` describes a planned action, action type, risk level, read-only status, confirmation need, and optional command text.
- `PolicyDecision` records whether the action is allowed, blocked, dry-run only, or requires confirmation.
- `SafetyPolicy` applies conservative rules: allow low-risk read-only actions, dry-run medium-risk actions, block destructive/high/critical actions by default, and support action/command allowlists and denylists.
- `ExecutionPlan` groups the adapter request, planned actions, and policy decisions.
- `SafeExecutionAdapter` wraps an adapter, evaluates planned actions, and returns an `ExpertResult` with policy metadata.

This is not a real sandbox. It does not isolate processes, execute commands, run subprocesses, scan networks, read files, or call external APIs.

### ExpertResult

`ExpertResult` stores structured output from an executor, adapter, or safe planning wrapper:

- module name
- task
- summary
- detail bullets
- confidence
- metadata, including backend and safety information when available

### Orchestrator

The orchestrator routes the task, builds focused context, optionally executes selected modules through direct executors or adapters, optionally wraps adapter execution with safety policy, and returns an `OrchestrationResult`.

Precedence is explicit:

1. `ExpertExecutorRegistry`
2. `ExecutionAdapterRegistry`
3. handoff-only behavior

Safety policy applies only to adapter execution when provided.

## Request Lifecycle

1. User task enters the system.
2. Router selects relevant modules.
3. Adaptive routing may adjust scores from feedback history.
4. ContextBuilder prepares stub and memory context for selected modules.
5. Orchestrator prefers direct executors when provided.
6. Otherwise, Orchestrator can use adapters.
7. If safety is enabled, adapter actions are planned and evaluated before any adapter result is returned.
8. Expert results and safety metadata are collected into `OrchestrationResult`.
9. Missing executors/adapters are reported in metadata and summary.
10. Feedback can later record whether the route worked.

## Grape-Cluster Metaphor

- Router selects the relevant grapes/modules.
- Memory modules provide relevant knowledge.
- ContextBuilder prepares focused context.
- Expert executors are tiny working grapes that can respond directly.
- Execution adapters are stems from grapes to future execution backends.
- Safety policy is protective skin around risky grapes.
- Orchestrator coordinates the selected path and backend choice.
- Feedback remembers which execution routes worked.

## Future Execution Backends

Future adapters may support local Python functions, local scripts, shell tools, local LLM wrappers, code analyzers, document processors, media analyzers, and cybersecurity scanners.

Before adding real execution, Grona still needs explicit safety design for sandboxing, subprocesses, file access, network access, secrets handling, and user consent.
