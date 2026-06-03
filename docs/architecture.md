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
   |
   | RoutingDecision
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
   |
   v
Merged result + route trace
   |
   v
+---------------+
| FeedbackLayer |
+---------------+
```

## Components

### Router

The router receives a user task, classifies its intent or domain, and chooses which modules should activate. In the first prototype, the router uses simple keyword and domain matching. Later versions may use embeddings, learned routing, memory-aware policies, or hybrid strategies.

The router should return an explainable decision: selected modules, skipped modules, scores, and reasons.

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

The feedback layer records what route was selected, which modules succeeded or failed, and whether the result was useful. It does not need to be complex at first. Even simple route traces can help identify weak routing rules or unreliable modules.

Future feedback can support adaptive routing, module scoring, and replacement decisions.

## Request Lifecycle

1. User task enters the system.
2. Router classifies the task using registry metadata.
3. Relevant modules are selected and irrelevant modules are skipped.
4. ContextBuilder gathers only route-relevant context.
5. Orchestrator invokes selected experts in the correct order.
6. Results are merged into a response with a visible route trace.
7. FeedbackLayer stores route outcome and module performance signals.

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

Skipped modules
- code-assistant
  Reason: no code or software maintenance signals
- media-video-tool
  Reason: no video editing or media workflow signals
- document-search
  Reason: no document corpus or search request signals
- cybersecurity-scanner
  Reason: no security, network, malware, or vulnerability signals
```

The important property is not that the first router is smart. The important property is that the system makes a sparse, inspectable choice and avoids activating unrelated capabilities.

## Design Principles

- Do not activate the whole brain for every problem.
- Route first, think second.
- Prefer small specialized components where possible.
- Keep selected and skipped modules explainable.
- Keep modules replaceable and versionable.
- Prefer local-first architecture where possible.
- Support heterogeneous experts: models, scripts, databases, search indexes, tools, and APIs.
- Let the system grow organically, like a grape cluster.
