# Architecture

Grona is a modular sparse AI architecture. Its core design goal is to route each task to the smallest useful set of modules instead of activating every model, memory region, tool, and context source for every request.

## System Diagram

```text
WorkspaceProfile -> filtered ModuleRegistry -> Router
        |                                      |
        v                                      v
WorkspaceConfig                         RoutingDecision
        |                                      |
        v                                      v
Raw text -> DocumentSource -> DocumentChunk -> MemoryRecord -> Memory Module
                                                              |
User task ---------------------------------> ContextBuilder --+-> Orchestrator
                                                                 |
                                                                 v
                                                            Expert Results
```

## Workspace Layer

A workspace is a configured vineyard for one use case.

- `WorkspaceProfile` describes enabled modules, domains, memory sources, tool profiles, routing mode, adaptive defaults, safety defaults, and metadata.
- `WorkspaceConfig` wraps a profile with optional routing, context, safety, memory, tool, and metadata settings.
- `filter_modules_for_workspace()` returns a filtered registry without mutating the original registry.

Profiles affect routing by narrowing the module registry before `Router` scores modules. If a profile filters modules, Grona preserves `general-reasoning` as a fallback when available.

This is not production config management. No workspace directories, disk-loaded config files, secrets, or external config services are implemented.

## Document Ingestion Stub

The document ingestion stub prepares future local document workflows without adding real RAG infrastructure.

- `DocumentSource` stores in-memory raw text with an id, title, source type, content, and metadata.
- `DocumentChunk` stores a deterministic chunk with source id, content, index, extracted keywords, assigned domains, and metadata.
- `TextChunker` splits normalized text into max-character chunks with overlap and practical word-boundary handling.
- `DocumentIngestor` converts sources into chunks, chunks into `MemoryRecord` values, and sources into an `InMemoryKeywordMemory` module.

This is not a filesystem crawler, PDF parser, OCR pipeline, embedding model, or vector database. It is deterministic text-to-memory preparation.

## Memory Modules and ContextBuilder

`MemoryRecord` stores small knowledge items with domains, keywords, source, and metadata. `InMemoryKeywordMemory` searches these records by deterministic keyword/domain overlap.

`ContextBuilder` combines route-specific stub context with memory context from relevant memory modules. Ingested document chunks become memory records, so they flow through the same context path as other memory.

## Execution, Tools, and Safety

`ExecutableExpert` is the direct execution contract. `ExecutionAdapter` bridges a selected expert module to a concrete execution backend. `ToolAdapter` models future tool use without performing it.

The safety layer evaluates planned actions before any future adapter can run a real tool:

- `ToolAction`
- `PolicyDecision`
- `SafetyPolicy`
- `ExecutionPlan`
- `SafeExecutionAdapter`
- `SafeToolRunner`

This is not a real sandbox. It does not isolate processes, execute commands, run subprocesses, scan networks, read files, write files, or call external APIs.

## Request Lifecycle

1. CLI or caller selects a `WorkspaceProfile`.
2. Grona filters the module registry for the workspace.
3. Raw demo document text may be converted into memory records.
4. User task enters the system.
5. Router selects relevant modules from the workspace registry.
6. Adaptive routing may adjust scores from feedback history.
7. ContextBuilder prepares stub and memory context for selected modules.
8. Orchestrator can hand off, run deterministic experts, or use deterministic adapters.
9. If safety is enabled, adapter actions are planned and evaluated before any adapter result is returned.
10. If demo tools are enabled, selected adapter modules can request deterministic mock tool results.
11. Expert results, tool summaries, and safety metadata are collected into `OrchestrationResult`.

## Grape-Cluster Metaphor

- Workspace is the vineyard/environment.
- Profile is how the cluster is arranged for a specific use case.
- Enabled modules are active grapes.
- Memory sources are knowledge nutrients.
- Safety policy is the protective layer.
- Routing config is the growth/activation rule set.
