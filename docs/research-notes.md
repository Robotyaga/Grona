# Research Notes

Grona explores sparse modular AI systems inspired by grape-cluster-like expert activation. These notes are conceptual and intentionally honest about what the project does not solve yet.

## Working Hypothesis

A useful AI assistant does not need to activate every capability for every request. If modules have clear metadata, scoped memory, inspectable context boundaries, and visible orchestration, a router can activate a small relevant subset and keep the rest dormant.

This may improve efficiency, explainability, replaceability, and local-first control. It may also introduce new problems: routing errors, brittle module metadata, incomplete context, coordination overhead, and feedback loops that reinforce bad routes.

## Sparse Activation

Sparse activation is the principle that only a subset of available capacity should run for a given input. For Grona, sparsity should be visible outside the model:

- Which modules were selected?
- Which modules were skipped?
- Why did the router make that choice?
- What context was prepared for the selected modules?
- Did feedback later suggest that route was useful?

The first prototype implements simple keyword/domain sparsity plus deterministic context stubs. It is a starting point, not a final routing or retrieval strategy.

## Routing

Routing is the central research problem. A router must balance relevance, cost, confidence, safety, memory availability, and task complexity.

Early routing can be rule-based. Later routing may combine rules, embeddings, learned classifiers, route history, and feedback. The risk is that routing becomes another opaque model. Grona should preserve route traces wherever possible.

## Context Building

Context building is separate from routing. Routing chooses the relevant branches and grapes. Context building gathers only the information needed by those selected grapes.

The current `ContextBuilder` uses built-in deterministic stubs for code, automotive diagnostics, cybersecurity, media/video, document search, and general reasoning. This is not retrieval. It is a scaffold for future local memory, document search, or tool-specific context gathering.

Open questions:

- How much context should each module receive?
- How should context relevance be scored?
- How should skipped context be audited?
- When should context be shared across modules versus kept module-specific?

## Orchestration

The current orchestrator does not execute real experts. It routes, builds focused context, and returns a structured handoff. This keeps the prototype honest while establishing where execution coordination will later live.

Future orchestration may decide call order, tool execution, retries, partial failures, and result synthesis. Those behaviors should not be hidden behind a single opaque call.

## Feedback and Adaptive Routing

Feedback is the first step toward adaptive routing, but it is not the same as learning. The current feedback layer records route decisions and optional outcomes. Adaptive routing can apply small bounded boosts or penalties when explicitly enabled.

Automatic route changes need careful evaluation because a bad feedback loop could reinforce weak routing instead of improving it.

## Retrieval-Augmented Generation

RAG usually retrieves relevant context and passes it to a model. Grona can use RAG as one kind of memory module, but it should not load every memory source for every task.

A route may decide that document search is relevant, then a future context builder can retrieve only the needed snippets. Another route may skip retrieval entirely.

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

### Route-Scoped Context Stubs

Use deterministic context stubs to inspect whether selected modules receive relevant, focused context before adding real retrieval.

### Route Trace Review

Inspect selected and skipped modules for each task. Use surprising routes to improve metadata and scoring.

### Feedback Simulation

Record which routes looked correct and which modules were missing. Use that data to design better routing experiments rather than changing routes automatically.

### Adaptive Scoring Baseline

Use conservative score boosts and penalties from feedback history. Check whether the explanations make sense before increasing adjustment strength or trying learned routing.
