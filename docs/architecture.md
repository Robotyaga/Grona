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
+----------------+       +--------------+
| ContextBuilder | <---- | MemoryModule |
+----------------+       +--------------+
   |
   v
+--------------+
| Orchestrator |
+--------------+
   |
   v
+-------------------------------+
| Selected ExpertModules only   |
+-------------------------------+
```

## Components

### Router

The router receives a user task, classifies its intent or domain, and chooses which modules should activate. In the first prototype, the router uses simple keyword and domain matching. Later versions may use embeddings, learned routing, memory-aware policies, or hybrid strategies.

The router returns an explainable decision: selected modules, skipped modules, base scores, final scores, and reasons.

### Adaptive Layer

The adaptive layer is an opt-in scoring adjustment that uses route history. It is not neural learning and does not replace the base router.

When enabled, it reads feedback records and builds per-module statistics: times selected, successes, failures, average rating, success rate, and average confidence. Modules with positive history can receive a small score boost. Modules with negative history can receive a small penalty.

Adaptive routing is intentionally conservative:

- It is disabled by default.
- Adjustments are bounded by `max_adjustment`.
- It never selects a module that has no base relevance only because of history.
- It explains the base score, adaptive adjustment, final score, and feedback summary.

### ExpertModule

An expert module is a specialized component with metadata and an invocation method. It may eventually wrap many different kinds of capability:

- local or remote LLMs
- scripts
- command-line tools
- databases
- vector indexes
- search APIs
- code analyzers
- media processors
- cybersecurity tools
- domain-specific reasoning modules

The first prototype uses mock expert modules so routing behavior stays easy to inspect.

### ModuleRegistry

The module registry stores available modules and their metadata: name, domain, capabilities, keywords, cost, and callable handler. It is the system's catalog of grapes in the cluster.

A future registry should support adding, disabling, replacing, and versioning modules without forcing the whole system to be rebuilt.

### ContextBuilder

The context builder gathers only the information needed by the selected modules. Its role is to avoid dumping every memory region, tool description, or document into one giant prompt.

In future versions, it may collect snippets from vector memory, SQL tables, local files, structured notes, or API responses based on the route.

### Orchestrator

The orchestrator executes the selected route. It decides call order, passes built context to modules, handles failures, and merges outputs into a final response.

The orchestrator should be boring and explicit: it should make the route visible rather than hiding the system's behavior behind a single opaque call.

### MemoryModule

A memory module stores domain-specific knowledge. It can be implemented as a vector store, SQL database, local file index, text search index, structured notebook, API cache, or domain graph.

Memory should be modular. A code assistant memory should not automatically load automotive diagnostic notes unless the route calls for it.

### FeedbackLayer

The feedback layer records what route was selected, which modules succeeded or failed, and whether the result was useful.

The first implementation stores `FeedbackRecord` values with task text, selected modules, skipped modules, confidence, a route summary, timestamp, optional rating, optional success/failure, optional notes, and optional metadata. Records can be kept in memory for tests and demos or appended to JSONL for local route history.

This fits the grape-cluster metaphor: the system can remember which branches and grapes were useful without making every future request activate the whole cluster.

### Route History

Route history is the saved trail of feedback records. The current summary functions can report:

- total feedback records
- most selected modules
- average confidence
- success count when success flags exist
- failure count when success flags exist

The adaptive layer can read this history and apply transparent score adjustments. It still does not perform real machine learning.

## Request Lifecycle

1. User task enters the system.
2. Router classifies the task using registry metadata.
3. Base module scores are computed from task/domain/keyword/capability matches.
4. If adaptive routing is enabled, route history can slightly adjust relevant module scores.
5. Relevant modules are selected and irrelevant modules are skipped.
6. ContextBuilder gathers only route-relevant context.
7. Orchestrator invokes selected experts in the correct order.
8. Results are merged into a response with a visible route trace.
9. FeedbackLayer can store route outcome and module performance signals.
10. Route history can be summarized for later inspection or future adaptive routing.

## Concrete Example

User asks: "Analyze why my car engine overheats after idling in traffic, and suggest what to inspect first."

A Grona-style route might activate:

```text
Selected modules
- automotive-diagnostics
  Reason: matched car, engine, overheats, idling, inspect
- maintenance-memory
  Reason: automotive troubleshooting notes are relevant
- safety-advisor
  Reason: overheating can involve risk and urgent stop conditions
```

If route history shows that `automotive-diagnostics` had several successful previous routes, adaptive routing might add a small boost:

```text
Base score 5.00; adaptive boost +0.15; final score 5.15
```

If history shows repeated failures, it might apply a small penalty:

```text
Base score 5.00; adaptive penalty -0.15; final score 4.85
```

The important property is not that the first adaptive layer is smart. The important property is that the system makes a sparse, inspectable choice, avoids activating unrelated capabilities, and can transparently account for past route outcomes.

## Design Principles

- Do not activate the whole brain for every problem.
- Route first, think second.
- Prefer small specialized components where possible.
- Keep selected and skipped modules explainable.
- Keep modules replaceable and versionable.
- Prefer local-first architecture where possible.
- Store feedback before attempting adaptive routing.
- Keep adaptive routing opt-in, bounded, and transparent.
- Support heterogeneous experts: models, scripts, databases, search indexes, tools, and APIs.
- Let the system grow organically, like a grape cluster.
