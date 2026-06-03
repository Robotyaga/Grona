# Research Notes

Grona explores sparse modular AI systems inspired by grape-cluster-like expert activation. These notes are conceptual and intentionally honest about what the project does not solve yet.

## Working Hypothesis

A useful AI assistant does not need to activate every capability for every request. If modules have clear metadata, scoped memory, and inspectable invocation boundaries, a router can activate a small relevant subset and keep the rest dormant.

This may improve efficiency, explainability, replaceability, and local-first control. It may also introduce new problems: routing errors, brittle module metadata, coordination overhead, and incomplete context.

## Mixture of Experts

Mixture of Experts shows that sparse expert activation can scale neural systems by routing tokens or examples to selected expert layers. Grona borrows the sparse activation intuition but applies it at a broader system level.

In Grona, an expert is not necessarily a neural layer. It can be a model, script, retriever, database, search index, local file tool, API wrapper, or domain-specific workflow.

## Sparse Activation

Sparse activation is the principle that only a subset of available capacity should run for a given input. For Grona, sparsity should be visible outside the model:

- Which modules were selected?
- Which modules were skipped?
- Why did the router make that choice?
- What was the cost of the selected route?
- Did the selected route work?

The first prototype implements only simple keyword/domain sparsity. It is a starting point, not a final routing strategy.

## Modular Agents

Agentic systems often combine models, tools, memory, and planning loops. Grona overlaps with that world but focuses on module selection and replaceability before complex autonomy.

A Grona module should be understandable in isolation. The system should be able to disable or replace one module without rewriting the whole assistant.

## Routing

Routing is the central research problem. A router must balance relevance, cost, confidence, safety, memory availability, and task complexity.

Early routing can be rule-based. Later routing may combine rules, embeddings, learned classifiers, route history, and feedback. The risk is that routing becomes another opaque model. Grona should preserve route traces wherever possible.

## Feedback and Route History

Feedback is the first step toward adaptive routing, but it is not the same as learning. The current feedback layer only records route decisions and optional outcomes. It can summarize which modules were selected most often, average confidence, and success/failure counts when those flags are available.

This route history may later support questions such as:

- Which branches and modules are repeatedly useful?
- Which modules are selected often but rated poorly?
- Which task types produce low confidence routes?
- Which skipped modules later turned out to be important?

For now, feedback should remain passive and inspectable. Automatic route changes need careful evaluation because a bad feedback loop could reinforce weak routing instead of improving it.

## Local-First AI

A local-first architecture keeps sensitive data, personal knowledge, and domain-specific tools close to the user when possible. Grona is well suited to local-first experiments because modules can wrap local files, local databases, local models, and local scripts.

Local-first does not mean local-only. Some routes may call remote APIs or hosted models, but that should be an explicit module decision rather than an invisible default.

## Retrieval-Augmented Generation

RAG usually retrieves relevant context and passes it to a model. Grona can use RAG as one kind of memory module, but it should not load every memory source for every task.

A route may decide that document search is relevant, then a context builder can retrieve only the needed snippets. Another route may skip retrieval entirely and use a local script or diagnostic tool.

## Memory Graphs

Memory graphs may help connect related entities, tasks, tools, documents, and outcomes. In a Grona system, a memory graph could support routing by answering questions like:

- Which modules have solved similar tasks?
- Which documents are connected to this domain?
- Which tools depend on this data source?
- Which route failed for a similar request?

This is future work. The first prototype does not implement memory graphs.

## Open Research Questions

- How should module metadata be represented so routing is reliable but not brittle?
- When should the router choose one specialist versus several complementary experts?
- How can a system recover when the router skips the right module?
- How should module cost, latency, privacy, and accuracy influence selection?
- What feedback signals are useful without requiring constant manual labeling?
- Can route traces improve trust without overwhelming the user?
- How should local memories be scoped to modules and domains?
- When does modularity add too much coordination overhead?
- How can route history improve routing without creating a self-reinforcing failure loop?

## Near-Term Experiments

### Keyword Routing Baseline

Start with transparent keyword/domain matching. Use it as a baseline for later embedding or learned routing.

### Heterogeneous Mock Modules

Represent code, automotive diagnostics, cybersecurity, media, and document search modules with simple metadata. Confirm that different tasks activate different modules.

### Route Trace Review

Inspect selected and skipped modules for each task. Use surprising routes to improve metadata and scoring.

### Feedback Simulation

Before building a full adaptive feedback layer, record which routes looked correct and which modules were missing. Use that data to design better routing experiments rather than changing routes automatically.
