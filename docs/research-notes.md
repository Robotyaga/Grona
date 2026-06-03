# Research Notes

Grona explores sparse modular AI systems inspired by grape-cluster-like expert activation. These notes are conceptual and intentionally honest about what the project does not solve yet.

## Working Hypothesis

A useful AI assistant does not need to activate every capability for every request. If modules have clear metadata, scoped memory, inspectable context boundaries, and visible orchestration, a router can activate a small relevant subset and keep the rest dormant.

This may improve efficiency, explainability, replaceability, and local-first control. It may also introduce new problems: routing errors, brittle module metadata, incomplete context, weak retrieval, coordination overhead, and feedback loops that reinforce bad routes.

## Sparse Activation

Sparse activation is the principle that only a subset of available capacity should run for a given input. For Grona, sparsity should be visible outside the model:

- Which modules were selected?
- Which modules were skipped?
- Why did the router make that choice?
- What context was prepared for the selected modules?
- Which context came from stubs versus memory modules?
- Did feedback later suggest that route was useful?

## Memory Modules

Memory modules are small knowledge pockets attached to parts of the cluster. They are different from feedback stores:

- Feedback stores remember route outcomes.
- Memory modules provide knowledge records for context building.

The current memory implementation is deliberately simple. `InMemoryKeywordMemory` matches `MemoryRecord` values by deterministic keyword, domain, capability, and content overlap. It returns `ContextItem` values with source metadata and relevance scores.

This is not semantic search. There are no embeddings, vector databases, SQL databases, memory graphs, real document ingestion, or external APIs yet.

## Context Building

Context building is separate from routing. Routing chooses the relevant branches and grapes. Context building gathers only the information needed by those selected grapes.

The context builder can now combine deterministic built-in stubs with memory-derived context. It still keeps the output small and traceable.

Open questions:

- How much memory context should each route receive?
- How should relevance be scored across different memory modules?
- How should duplicate or stale memory records be handled?
- When should memory be module-specific versus shared across domains?
- How should future retrieval be evaluated against this keyword baseline?

## Orchestration

The current orchestrator does not execute real experts. It routes, builds focused context, and returns a structured handoff. This keeps the prototype honest while establishing where execution coordination will later live.

Future orchestration may decide call order, tool execution, retries, partial failures, and result synthesis. Those behaviors should not be hidden behind a single opaque call.

## Retrieval-Augmented Generation

RAG usually retrieves relevant context and passes it to a model. Grona can use RAG as one kind of memory module, but it should not load every memory source for every task.

A route may decide that document search is relevant, then a future memory module can retrieve only the needed snippets. Another route may skip retrieval entirely.

## Memory Graphs

Memory graphs may help connect related entities, tasks, tools, documents, and outcomes. In a Grona system, a memory graph could support routing and context building by answering questions like:

- Which modules have solved similar tasks?
- Which documents are connected to this domain?
- Which tools depend on this data source?
- Which route failed for a similar request?

This is future work. The current prototype does not implement memory graphs.

## Near-Term Experiments

### Keyword Routing Baseline

Start with transparent keyword/domain matching. Use it as a baseline for later embedding or learned routing.

### Keyword Memory Baseline

Use deterministic keyword/domain memory records to inspect whether selected modules receive useful focused context before adding vector search or semantic retrieval.

### Route Trace Review

Inspect selected and skipped modules for each task. Use surprising routes to improve metadata, memory records, and scoring.

### Feedback Simulation

Record which routes looked correct and which modules were missing. Use that data to design better routing experiments rather than changing routes automatically.

### Adaptive Scoring Baseline

Use conservative score boosts and penalties from feedback history. Check whether the explanations make sense before increasing adjustment strength or trying learned routing.
