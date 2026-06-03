# Research Notes

Grona explores sparse modular AI systems inspired by grape-cluster-like expert activation. These notes are conceptual and intentionally honest about what the project does not solve yet.

For the longer direction, see [Project vision](project-vision.md). For implementation boundaries, see [Architecture](architecture.md), [Development notes](development.md), and [Roadmap](roadmap.md).

## Working Hypothesis

A useful AI assistant does not need to activate every capability for every request. If modules have clear metadata, scoped memory, inspectable context boundaries, visible orchestration, typed execution contracts, backend adapters, tool boundaries, deterministic ingestion, workspace profiles, and safety policy checks, a router can activate a small relevant subset and keep the rest dormant.

## Why This Differs From Monolithic Execution

A monolithic system often hides which capability, memory, prompt, or tool surface shaped the result. Grona explores visible routing instead:

- which modules were considered
- which modules were skipped
- which scores and reasons mattered
- which context was attached
- which safety policy decisions were made
- which feedback might alter future routing

The current prototype is deterministic so these questions can be inspected before adding model uncertainty.

## Workspace Profiles

A workspace profile describes a configured vineyard for a specific use case.

- Workspace is the environment.
- Profile is how the cluster is arranged.
- Enabled modules are active grapes.
- Memory sources are knowledge nutrients.
- Safety policy is the protective layer.
- Routing mode is the activation rule set.

`WorkspaceProfile` and `WorkspaceConfig` are intentionally small dataclass-based structures. They are serializable to dict/JSON so a profile can be reproduced in tests and examples. Built-in profiles cover default, code, cybersecurity, media, automotive, and document research workflows.

The current layer filters the module registry before routing. This helps test whether the same task routes differently under different project assumptions.

This is not production config management. There is no persisted workspace directory, no disk-loaded config file, no secrets handling, no external API, and no database-backed profile system.

## Document Ingestion Stub

Document ingestion explores a simple path from raw text to route-scoped memory:

```text
Raw document text -> DocumentSource -> DocumentChunk -> MemoryRecord -> InMemoryKeywordMemory -> ContextBuilder
```

The current implementation is deliberately not RAG. It has no embeddings, semantic search, vector database, PDF parsing, OCR, filesystem crawler, file watcher, or external API.

## Knowledge Before Weights

Grona assumes that some knowledge should remain external, structured, source-aware, and validated before it ever becomes training data or expert behavior.

This motivates future `KnowledgeSeed` and `KnowledgeValidator` work: collect knowledge with provenance, test whether it is useful, and only then decide whether it should influence routing, memory, prompts, benchmarks, or training exports.

## Execution and Tool Boundaries

The execution interface separates routing metadata from runnable behavior. Execution adapters add a backend-oriented layer. Tool adapters model future tool use without performing it.

The current mock tools do not read files, write files, run commands, start subprocesses, call networks, use external APIs, or invoke real scanners. They make future integration points visible and testable.

## Safety Policy Layer

The safety layer asks policy questions before future tools exist:

- Is this action allowed?
- Is it risky, destructive, or unknown?
- Is it read-only?
- Should it remain dry-run only?
- What confirmation would be required?
- Why was it allowed or blocked?

`ToolAction` is a planned action, not execution. `PolicyDecision` is the reasoned result of policy evaluation. `ExecutionPlan` groups planned actions and decisions for an `ExecutionRequest`. `SafeExecutionAdapter` wraps an adapter and turns policy outcomes into `ExpertResult` values. `SafeToolRunner` applies the same policy idea to mock tool adapters.

## Future Growth Questions

- Can workspace profiles reliably constrain routing behavior?
- Can feedback improve routing without turning into opaque learning?
- Can external knowledge seeds improve modules without being baked into weights too early?
- Can donor model outputs be validated before becoming durable knowledge?
- Can benchmark traces expose regressions in routing, context, and safety behavior?
- Can a GrowthEngine propose useful changes while staying auditable?

## Current Limits

- No persisted workspace directory yet.
- No external config files loaded from disk.
- No secrets or user-specific private settings.
- No production config management.
- No real AI expert execution yet.
- No real RAG yet.
- No PDF parsing, OCR, embeddings, vector search, or filesystem crawling yet.
- No shell execution, subprocess usage, network calls, or sandboxing yet.
- No process isolation or filesystem isolation.
- No OpenAI API or Ollama integration.
- No vector database, SQL database, web server, or external API.
- No production orchestration.

## Future Work

Before adding persisted workspace support, Grona needs explicit designs for profile file format, migration/versioning, local path boundaries, secrets policy, and user confirmation.

Before adding real document workflows, Grona needs explicit designs for file selection, parser dependencies, citation tracking, content updates, embeddings, vector search, privacy boundaries, and deletion semantics.

Before adding real execution, Grona needs explicit designs for subprocess control, sandboxing, file access boundaries, network access boundaries, secrets handling, audit logs, user confirmation flows, and rollback or recovery expectations.
