# Architecture

Grona is a modular sparse AI architecture. Its core design goal is to route each task to the smallest useful set of modules instead of activating every model, memory region, tool, and context source for every request.

## System Diagram

```text
Raw text -> DocumentSource -> DocumentChunk -> MemoryRecord -> Memory Module
                                                              |
User task -> Router -> RoutingDecision -> ContextBuilder -----+-> Orchestrator
              ^                    ^                              |
              |                    |                              v
       Adaptive Routing       Memory Modules                 Expert Results
              ^                                                   ^
              |                                                   |
        Feedback Layer                  Executors, Adapters, Tool Adapters, Safety Policy
```

## Components

### ExpertModule

`ExpertModule` is routing metadata: name, domain, capabilities, keywords, cost, and demo handler. It tells the router which grapes exist and when they might be relevant.

### Document Ingestion Stub

The document ingestion stub prepares future local document workflows without adding real RAG infrastructure.

- `DocumentSource` stores in-memory raw text with an id, title, source type, content, and metadata.
- `DocumentChunk` stores a deterministic chunk with source id, content, index, extracted keywords, assigned domains, and metadata.
- `TextChunker` splits normalized text into max-character chunks with overlap and practical word-boundary handling.
- `DocumentIngestor` converts sources into chunks, chunks into `MemoryRecord` values, and sources into an `InMemoryKeywordMemory` module.
- `create_demo_document_sources()` provides small in-memory demo sources for automotive, code, cybersecurity, media, and document indexing tasks.

This is not a filesystem crawler, PDF parser, OCR pipeline, embedding model, or vector database. It is deterministic text-to-memory preparation.

### Memory Modules and ContextBuilder

`MemoryRecord` stores small knowledge items with domains, keywords, source, and metadata. `InMemoryKeywordMemory` searches these records by deterministic keyword/domain overlap.

`ContextBuilder` combines route-specific stub context with memory context from relevant memory modules. Ingested document chunks become memory records, so they flow through the same context path as other memory.

### ExecutableExpert

`ExecutableExpert` is the direct execution contract. It is separate from `ExpertModule` so metadata and execution can evolve independently. The current executors are deterministic demos.

### ExecutionRequest and ExecutionAdapter

`ExecutionRequest` normalizes the task, selected module name, route-scoped context, and metadata passed to an adapter.

`ExecutionAdapter` is a bridge between a selected expert module and a concrete execution backend. Future adapters could wrap local Python functions, scripts, shell tools, local LLM wrappers, code analyzers, document processors, media analyzers, or cybersecurity scanners. The current adapters are deterministic and safe only.

### Tool Adapter Prototype

The tool adapter layer introduces a small, explicit boundary for future tool-like capabilities without real tool execution.

- `ToolSpec` describes a mock tool: name, description, action type, risk level, read-only status, input schema, and metadata.
- `ToolRequest` records which mock tool was requested, the task, input values, request source, and metadata.
- `ToolResult` stores deterministic mock output and can be rendered with `to_text()`.
- `ToolAdapter` is the protocol for planning a `ToolAction` and returning a `ToolResult`.
- `MockToolAdapter` is deterministic and never touches files, networks, subprocesses, shell commands, external APIs, or real scanners.
- `ToolRegistry` registers and finds mock tool adapters by name, action type, or metadata.
- `SafeToolRunner` asks an adapter for a planned `ToolAction`, evaluates it with `SafetyPolicy`, and only then returns a `ToolResult`.

The current tool adapters are demo-only. They produce traceable mock output so the orchestration contract can be tested before real tools exist.

### Safety Policy Layer

The safety layer evaluates planned actions before any future adapter can run a real tool.

- `ToolAction` describes a planned action, action type, risk level, read-only status, confirmation need, and optional command text.
- `PolicyDecision` records whether the action is allowed, blocked, dry-run only, or requires confirmation.
- `SafetyPolicy` applies conservative rules: allow low-risk read-only actions, dry-run medium-risk actions, block destructive/high/critical actions by default, and support action/command allowlists and denylists.
- `ExecutionPlan` groups the adapter request, planned actions, and policy decisions.
- `SafeExecutionAdapter` wraps an adapter, evaluates planned actions, and returns an `ExpertResult` with policy metadata.

This is not a real sandbox. It does not isolate processes, execute commands, run subprocesses, scan networks, read files, write files, or call external APIs.

### ExpertResult

`ExpertResult` stores structured output from an executor, adapter, or safe planning wrapper: module name, task, summary, detail bullets, confidence, and metadata.

### Orchestrator

The orchestrator routes the task, builds focused context, optionally executes selected modules through direct executors or adapters, optionally wraps adapter execution with safety policy, optionally requests deterministic mock tool results, and returns an `OrchestrationResult`.

## Request Lifecycle

1. Raw demo document text can be converted into `DocumentSource` values.
2. `DocumentIngestor` chunks sources and converts chunks to `MemoryRecord` values.
3. `InMemoryKeywordMemory` stores the records for deterministic retrieval.
4. User task enters the system.
5. Router selects relevant modules.
6. Adaptive routing may adjust scores from feedback history.
7. ContextBuilder prepares stub and memory context for selected modules.
8. Orchestrator prefers direct executors when provided.
9. Otherwise, Orchestrator can use adapters.
10. If safety is enabled, adapter actions are planned and evaluated before any adapter result is returned.
11. If demo tools are enabled, selected adapter modules can request deterministic mock tool results through `SafeToolRunner`.
12. Expert results, tool summaries, and safety metadata are collected into `OrchestrationResult`.
13. Missing executors/adapters/tools are reported in metadata and summary.
14. Feedback can later record whether the route worked.

## Grape-Cluster Metaphor

- Documents are nutrient sources.
- Ingestion breaks them into small digestible pieces.
- Memory modules store those pieces near relevant branches.
- Router selects the relevant grapes/modules.
- ContextBuilder retrieves only the pieces relevant to the selected route.
- Expert executors are tiny working grapes that can respond directly.
- Execution adapters are stems from grapes to future execution backends.
- Tool adapters are mock tool grapes with explicit safety checks.
- Safety policy is protective skin around risky grapes.
- Feedback remembers which execution routes worked.

## Future Execution Backends

Future adapters may support local Python functions, local scripts, shell tools, local LLM wrappers, code analyzers, document processors, media analyzers, and cybersecurity scanners.

Before adding real execution, Grona still needs explicit safety design for sandboxing, subprocesses, file access, network access, secrets handling, and user consent. Before adding real document workflows, Grona still needs explicit designs for file boundaries, parsers, indexing, embeddings, citations, and update behavior.
