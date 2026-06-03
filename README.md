# Grona

Grona is a lightweight research prototype for a modular sparse AI architecture inspired by grape-cluster-like expert activation.

The core idea is simple: do not activate every capability for every task. Route a task through a workspace profile to relevant expert modules, gather focused context from stubs, memory modules, or ingested in-memory documents, optionally run deterministic demo experts or execution adapters, evaluate planned tool and mock tool actions with safety policy, and keep the trace visible.

## Architecture Metaphor

- Workspace profiles describe the vineyard: which grapes, nutrients, and protective defaults are active.
- The router chooses relevant branches and grapes.
- Documents are nutrient sources that can be split into small digestible chunks.
- Memory modules are small knowledge pockets attached to parts of the cluster.
- The context builder gathers only the information needed by selected grapes.
- The orchestrator coordinates the selected path.
- Demo expert executors are the first tiny working grapes that can return structured results.
- Execution adapters are bridges from selected grapes to future execution backends.
- Tool adapters are safe mock grapes for testing future tool boundaries.
- Safety policy is protective skin around risky grapes before any future tool use.
- The feedback layer remembers which paths worked.
- Adaptive routing slightly adjusts future activation from previous outcomes.

## Current Prototype

The current prototype includes:

- `WorkspaceProfile` and `WorkspaceConfig`: lightweight built-in project profile/config objects.
- `ExpertModule`: metadata used for routing and module identity.
- `ExecutableExpert`: a lightweight direct execution contract for runnable experts.
- `ExecutionAdapter`: a bridge from selected modules to future execution backends.
- `ExecutionRequest`: normalized task, module, context, and metadata input for adapters.
- `ToolAction`, `SafetyPolicy`, `PolicyDecision`, `ExecutionPlan`, and `SafeExecutionAdapter`.
- `ToolSpec`, `ToolRequest`, `ToolResult`, `ToolAdapter`, `MockToolAdapter`, `ToolRegistry`, and `SafeToolRunner`.
- `DocumentSource`, `DocumentChunk`, `TextChunker`, and `DocumentIngestor`.
- deterministic demo executors, deterministic demo adapters, deterministic mock tools, demo document sources, CLI, examples, tests, and CI.

The workspace, ingestion, demo execution, tool, and safety layers are deterministic proof-of-contract implementations. They are not real AI, real tooling, real RAG, production config management, or sandboxing.

## Install

```bash
pip install -e .
```

For tests and linting:

```bash
pip install -e .[dev]
```

## Run Demos

```bash
python examples/basic_routing_demo.py
python examples/feedback_demo.py
python examples/adaptive_routing_demo.py
python examples/orchestration_demo.py
python examples/memory_demo.py
python examples/expert_execution_demo.py
python examples/execution_adapters_demo.py
python examples/safety_policy_demo.py
python examples/tool_adapter_demo.py
python examples/document_ingestion_demo.py
python examples/workspace_profile_demo.py
```

## Run the CLI

Route a task:

```bash
python -m grona "Review firewall logs for suspicious port scans"
```

Use a built-in workspace profile:

```bash
python -m grona "Diagnose engine overheating" --workspace automotive
python -m grona "Review this Python script for security issues" --workspace cybersecurity
python -m grona "Plan MotionCam RAW workflow" --workspace media
python -m grona "Find document indexing notes" --workspace documents
```

Build context with demo memory or ingested demo documents:

```bash
python -m grona "Diagnose engine overheating" --orchestrate --use-demo-memory
python -m grona "Diagnose engine overheating" --orchestrate --ingest-demo-docs
```

Run deterministic demo adapters and mock tools:

```bash
python -m grona "Review this Python script for security issues" --orchestrate --use-demo-adapters
python -m grona "Review this project for security issues" --orchestrate --use-demo-adapters --safe
python -m grona "Review this project" --use-demo-adapters --dry-run-tools
python -m grona "Analyze engine overheating symptoms" --use-demo-tools
```

`--execute-demo-experts`, `--use-demo-adapters`, and `--use-demo-tools` imply orchestration if `--orchestrate` is omitted. Some workspace profiles also imply orchestration or safety by default. Explicit flags still enable the same behavior predictably.

## Workspace Profiles

A workspace profile is a lightweight in-memory project profile. It can describe enabled modules, enabled domains, memory sources, tool profiles, routing mode, adaptive defaults, safety defaults, and metadata.

Built-in workspaces:

- `default`: all default modules available.
- `code`: code and document-focused routing with adaptive routing enabled.
- `cybersecurity`: security, code, document, and general routing with safety enabled.
- `media`: media, document, and general workflow routing.
- `automotive`: automotive, document, and general routing with safety enabled.
- `documents`: document search, retrieval, and general routing.

This is not a persisted workspace directory or production config system. See `docs/workspaces.md` for details.

## Document Ingestion Stub

The document ingestion layer prepares future local document workflows without adding real RAG infrastructure.

```text
Raw document text -> DocumentSource -> DocumentChunk -> MemoryRecord -> InMemoryKeywordMemory -> ContextBuilder
```

This is in-memory deterministic text ingestion only. It does not parse PDFs, run OCR, crawl the filesystem, build embeddings, use a vector database, or call external APIs.

## Run Tests

```bash
pytest
```

Optional linting:

```bash
ruff check .
```

## Current Limitations

- Workspace profiles are built-in/in-memory only; no persisted workspace directory is implemented.
- No external config files are loaded from disk.
- No user-specific secrets or production config management.
- Demo executors, adapters, and mock tool adapters are deterministic stubs, not real AI reasoning.
- Document ingestion is in-memory deterministic text ingestion only.
- The router and memory retrieval are keyword/domain based.
- No PDF parsing, OCR, semantic embeddings, vector search, or filesystem crawler is implemented.
- The safety layer is policy/planning only, not a real sandbox.
- No shell commands, subprocess execution, sandboxing, real filesystem tools, or unsafe tools are implemented.
- No external tools, network requests, OpenAI API, Ollama integration, web server, vector database, SQL database, or external APIs.
- No production orchestration.

These limits are intentional. Grona is currently a research/prototype foundation for sparse modular AI architecture.
