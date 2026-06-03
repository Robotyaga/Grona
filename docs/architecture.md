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
+----------------+       +----------------+
| ContextBuilder | <---- | Memory Modules |
+----------------+       +----------------+
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

The router receives a user task, classifies its intent or domain, and chooses which modules should activate. In the first prototype, the router uses simple keyword and domain matching.

The router returns an explainable decision: selected modules, skipped modules, base scores, final scores, and reasons.

### Feedback Layer and Adaptive Routing

The feedback layer records what route was selected and whether the result was useful. Route history can be summarized and can slightly adjust future activation when adaptive routing is enabled.

Feedback is different from memory. Feedback stores route outcomes. Memory modules provide task/domain knowledge to the context builder.

### Memory Modules

Memory modules are small knowledge pockets attached to parts of the cluster. A `MemoryRecord` stores content, domains, keywords, source, and metadata. A `MemoryModule` returns `ContextItem` objects for a task and selected route.

The first implementation is `InMemoryKeywordMemory`. It ranks records by deterministic keyword, domain, capability, and content overlap. It does not use embeddings, vector search, semantic search, SQL, external APIs, or hidden model calls.

A `JsonlMemoryStore` can load and save records as JSONL and turn them into an in-memory keyword module. This is a convenience for small local experiments, not a production memory system.

### ContextBuilder

The context builder receives the routing decision and original task text. It gathers only route-relevant context for selected modules.

It can combine two sources:

- built-in deterministic stub context
- memory-derived context from relevant memory modules

The builder keeps context small with configurable limits and tags context sources so the orchestrator can show whether an item came from a stub or memory module.

### Orchestrator

The orchestrator coordinates the selected path. Today it routes the task, asks `ContextBuilder` for route-scoped context, and returns an `OrchestrationResult` with selected modules, context items, summary, and metadata.

It does not execute real experts yet. It prepares a structured handoff that a later execution layer could use.

## Request Lifecycle

1. User task enters the system.
2. Router classifies the task using registry metadata.
3. If adaptive routing is enabled, route history can slightly adjust relevant module scores.
4. Relevant modules are selected and irrelevant modules are skipped.
5. ContextBuilder prepares route-relevant stub context.
6. ContextBuilder asks only relevant memory modules for additional context.
7. Orchestrator returns a structured handoff with route, context, selected modules, and summary.
8. FeedbackLayer can store route outcome signals.

## Grape-Cluster Metaphor

- Router chooses the relevant branches and grapes.
- Memory modules are small knowledge pockets attached to parts of the cluster.
- ContextBuilder gathers only the information needed by selected grapes.
- Orchestrator coordinates the selected path.
- Feedback Layer remembers which paths worked.
- Adaptive Routing slightly adjusts future activation from previous outcomes.

## Design Principles

- Do not activate the whole brain for every problem.
- Route first, build focused context second.
- Keep memory retrieval deterministic and inspectable.
- Keep selected and skipped modules explainable.
- Keep context scoped to selected modules.
- Keep orchestration honest and non-production.
- Keep adaptive routing opt-in, bounded, and transparent.
