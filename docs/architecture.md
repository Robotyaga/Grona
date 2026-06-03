# Architecture

Grona is a modular sparse AI architecture. Its core design goal is to route each task to the smallest useful set of modules instead of activating every model, memory region, tool, and context source for every request.

## System Diagram

```text
User task
   |
   v
+--------+        +----------------+
| Router | <----> | ModuleRegistry |
+--------+        +----------------+
   |                    ^
   | RoutingDecision    |
   v                    |
+----------------+      |
| Adaptive Layer | <----+
+----------------+
   ^
   |
+----------------+       +----------------+
| FeedbackLayer  | ----> | Route History  |
+----------------+       +----------------+
   |
   v
+----------------+
| ContextBuilder |
+----------------+
   |
   v
+--------------+
| Orchestrator |
+--------------+
   |
   v
+--------------------------------+
| Structured handoff for later   |
| execution layer                |
+--------------------------------+
```

## Components

### Router

The router receives a user task, classifies its intent or domain, and chooses which modules should activate. In the first prototype, the router uses simple keyword and domain matching. Later versions may use embeddings, learned routing, memory-aware policies, or hybrid strategies.

The router returns an explainable decision: selected modules, skipped modules, base scores, final scores, and reasons.

### Adaptive Layer

The adaptive layer is an opt-in scoring adjustment that uses route history. It is not neural learning and does not replace the base router.

When enabled, it reads feedback records and builds per-module statistics. Modules with positive history can receive a small score boost. Modules with negative history can receive a small penalty.

### ContextBuilder

The context builder receives the routing decision and original task text. It gathers only route-relevant context for selected modules. In the current prototype, this context is built from deterministic stubs such as code review checklists, automotive diagnostic notes, cybersecurity review prompts, media workflow notes, document search notes, and general reasoning checklists.

This separation matters: routing decides which branches and grapes are relevant, while context building gathers only the nutrients those selected grapes need. It avoids dumping unrelated memory, tools, or documents into every task.

There is no real retrieval yet. Future versions may collect snippets from local files, document indexes, structured notes, memory graphs, databases, or APIs based on the route.

### Orchestrator

The orchestrator coordinates the selected path. Today it routes the task, asks `ContextBuilder` for route-scoped context, and returns an `OrchestrationResult` with selected modules, context items, summary, and metadata.

It does not execute real experts yet. It prepares a structured handoff that a later execution layer could use.

### ExpertModule

An expert module is a specialized component with metadata and an invocation method. The first prototype uses mock expert modules so routing behavior stays easy to inspect. Future modules may wrap local tools, scripts, databases, local models, search indexes, or APIs.

### FeedbackLayer and Route History

The feedback layer records what route was selected and whether the result was useful. Route history can be summarized and can slightly adjust future activation when adaptive routing is enabled.

This fits the grape-cluster metaphor: the system remembers which branches and grapes were useful without making every future request activate the whole cluster.

## Request Lifecycle

1. User task enters the system.
2. Router classifies the task using registry metadata.
3. Base module scores are computed from task/domain/keyword/capability matches.
4. If adaptive routing is enabled, route history can slightly adjust relevant module scores.
5. Relevant modules are selected and irrelevant modules are skipped.
6. ContextBuilder prepares only route-relevant stub context.
7. Orchestrator returns a structured handoff with route, context, selected modules, and summary.
8. FeedbackLayer can store route outcome and module performance signals.
9. Route history can be summarized for later inspection or future adaptive routing.

## Design Principles

- Do not activate the whole brain for every problem.
- Route first, build focused context second.
- Prefer small specialized components where possible.
- Keep selected and skipped modules explainable.
- Keep context scoped to selected modules.
- Keep orchestration honest and non-production.
- Store feedback before attempting adaptive routing.
- Keep adaptive routing opt-in, bounded, and transparent.
- Let the system grow organically, like a grape cluster.
