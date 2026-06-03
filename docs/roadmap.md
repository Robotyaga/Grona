# Roadmap

Grona should stay readable before adding heavier infrastructure.

## Phase 0: Concept and Documentation

- Define the grape-cluster architecture metaphor.
- Explain sparse modular activation.
- Establish a lightweight repository structure.

## Phase 1: Mock Router and Module Registry

- Implement `ExpertModule`, `ModuleRegistry`, `Router`, and `RoutingDecision`.
- Use simple keyword/domain matching.
- Show selected modules, skipped modules, scores, and reasons.

## Phase 2: Feedback Layer and Route History

- Add `FeedbackRecord` and simple route history stores.
- Summarize selected modules, confidence, and success/failure counts.

## Phase 3: Feedback-Informed Adaptive Routing

- Add opt-in adaptive routing configuration.
- Apply small bounded boosts or penalties from feedback history.
- Keep this deterministic, not neural learning.

## Phase 4: Context Builder and Orchestration Foundation

- Add `ContextItem`, `ContextBuilder`, `Orchestrator`, and `OrchestrationResult`.
- Keep orchestration as a structured handoff.

## Phase 5: Memory Modules and Retrieval Stubs

- Add `MemoryRecord`, `MemoryModule`, and deterministic keyword memory.
- Allow `ContextBuilder` to query relevant memory modules only.
- Keep this keyword retrieval, not embeddings or semantic search.

## Phase 6: Expert Execution Interface

- Add `ExpertResult` and `ExecutableExpert`.
- Add `ExpertExecutorRegistry`.
- Add deterministic demo executors for default modules.
- Allow `Orchestrator` to optionally execute selected demo experts.
- Keep this as proof of contract, not real AI execution.

## Phase 7: Execution Adapters

- Add `ExecutionRequest`, `ExecutionAdapter`, and `ExecutionAdapterRegistry`.
- Add deterministic `StaticExecutionAdapter` and `PythonFunctionAdapter` demos.
- Allow `Orchestrator` to optionally execute selected modules through adapters.
- Keep adapters safe: no subprocess, shell execution, external APIs, or LLM calls yet.

## Phase 8: Tool Safety Policy and Planning

- Add `ToolAction`, `PolicyDecision`, `SafetyPolicy`, and `ExecutionPlan`.
- Add `SafeExecutionAdapter` for adapter-side policy evaluation.
- Support dry-run planning, allowlists, denylists, and visible blocked reasons.
- Keep this as policy evaluation only, not sandboxing or execution.

## Phase 9: Safe Mock Tool Adapter Prototype

- Add `ToolSpec`, `ToolRequest`, and `ToolResult`.
- Add `ToolAdapter`, deterministic `MockToolAdapter`, `ToolRegistry`, and `SafeToolRunner`.
- Add `create_default_tool_registry()` for mock code, car diagnostics, cybersecurity, media/video, and document search tools.
- Allow selected adapter-backed modules to attach deterministic mock tool results.
- Keep this mock-only: no shell, subprocess, network, external APIs, real filesystem tools, or sandboxing claims.

## Phase 10: Document/File Ingestion Stub

- Add `DocumentSource`, `DocumentChunk`, `TextChunker`, and `DocumentIngestor`.
- Convert in-memory text sources into deterministic chunks, keyword/domain metadata, `MemoryRecord` values, and `InMemoryKeywordMemory` modules.
- Add `create_demo_document_sources()` for automotive, code, cybersecurity, media, and document indexing notes.
- Add CLI `--ingest-demo-docs` and a document ingestion example.
- Keep this in-memory only: no filesystem crawling, PDF parsing, OCR, embeddings, vector database, or external APIs.

## Phase 11: Workspace / Project Profile Layer

- Add `WorkspaceProfile` and `WorkspaceConfig`.
- Add deterministic dict/JSON serialization.
- Add built-in profiles for default, code, cybersecurity, media, automotive, and documents.
- Add registry filtering by enabled modules or enabled domains while preserving general fallback.
- Add CLI `--workspace` and workspace demo/docs.
- Keep this in-memory only: no persisted workspace directory, disk config loading, secrets, or production config management.

## Phase 12: Real Local Tools and Modules

- Replace selected mock/demo modules with simple local tools only after safety design matures.
- Add scripts for code inspection, file search, document parsing, or media metadata extraction only with explicit boundaries.
- Keep tool interfaces small and explicit.
- Add real sandboxing and safety design before any shell or subprocess backend.

## Phase 13: Memory and Feedback Integration

- Introduce module-specific local memory stores.
- Experiment with local text indexes or structured notes.
- Use feedback to evaluate routes, execution results, tool results, ingestion results, workspace profiles, and safety decisions.

## Phase 14: Local LLM Integration

- Add optional local LLM modules through adapter contracts.
- Route only selected tasks to LLM-backed experts.
- Keep prompts scoped to route-relevant context.

## Phase 15: Learned Routing Experiments

- Experiment with learned routing only after deterministic baselines are understood.
- Add route confidence calibration.
- Explore hierarchical routing: branch first, grape second.

## Phase 16: UI and API Layer

- Add UI/API only after routing, workspaces, context, memory, ingestion, execution, adapter, tool, and safety contracts are stable.
- Show workspace profile, route traces, context sources, expert results, adapter backends, mock tool results, safety plans, and feedback signals.
