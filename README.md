# Grona

Grona is a lightweight research prototype for a modular sparse AI architecture inspired by grape-cluster-like expert activation.

The core idea is simple: do not activate every capability for every task. Route a task to relevant expert modules, gather focused context from stubs, memory modules, or ingested in-memory documents, optionally run deterministic demo experts or execution adapters, evaluate planned tool and mock tool actions with safety policy, and keep the trace visible.

## Architecture Metaphor

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

- `ExpertModule`: metadata used for routing and module identity.
- `ExecutableExpert`: a lightweight direct execution contract for runnable experts.
- `ExecutionAdapter`: a bridge from selected modules to future execution backends.
- `ExecutionRequest`: normalized task, module, context, and metadata input for adapters.
- `ToolAction`: a planned future tool action that is never executed by this prototype.
- `SafetyPolicy` and `PolicyDecision`: deterministic policy evaluation for planned actions.
- `ExecutionPlan` and `SafeExecutionAdapter`: dry-run planning around execution adapters.
- `ToolSpec`, `ToolRequest`, and `ToolResult`: structured mock tool contracts.
- `ToolAdapter`, `MockToolAdapter`, `ToolRegistry`, and `SafeToolRunner`: deterministic tool adapter prototype with policy checks.
- `DocumentSource`, `DocumentChunk`, `TextChunker`, and `DocumentIngestor`: deterministic in-memory text ingestion into memory records.
- `ExpertResult`: structured deterministic output from executors, adapters, and tool summaries.
- deterministic demo executors, deterministic demo adapters, deterministic mock tools, and demo document sources.
- `Router`, `RoutingDecision`, feedback, adaptive routing, memory modules, context building, orchestration, CLI, examples, tests, and CI.

The demo executors, adapters, tool adapters, ingestion layer, and safety layer are not real AI, real tooling, real RAG, or sandboxing. They are deterministic proof-of-contract implementations.

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
```

## Run the CLI

Route a task:

```bash
python -m grona "Review firewall logs for suspicious port scans"
```

Build context with demo memory:

```bash
python -m grona "Diagnose engine overheating" --orchestrate --use-demo-memory
```

Build context from ingested in-memory demo documents:

```bash
python -m grona "Diagnose engine overheating" --orchestrate --ingest-demo-docs
```

Run deterministic demo adapters:

```bash
python -m grona "Review this Python script for security issues" --orchestrate --use-demo-adapters
```

Evaluate adapter planning with safety policy:

```bash
python -m grona "Review this project for security issues" --orchestrate --use-demo-adapters --safe
```

Force planned tool actions into dry-run mode:

```bash
python -m grona "Review this project" --use-demo-adapters --dry-run-tools
```

Run deterministic mock tool adapters through selected demo adapters:

```bash
python -m grona "Analyze engine overheating symptoms" --use-demo-tools
```

`--execute-demo-experts`, `--use-demo-adapters`, and `--use-demo-tools` imply orchestration if `--orchestrate` is omitted. If both execution options are supplied, explicit demo experts take precedence over adapters. `--use-demo-tools` enables demo adapters, creates the default mock tool registry, and evaluates mock tool plans with the default safety policy.

`--ingest-demo-docs` is used during orchestration. Without orchestration, the CLI routes normally and prints a note that document ingestion is only used with orchestration.

## Document Ingestion Stub

The document ingestion layer prepares future local document workflows without adding real RAG infrastructure.

- `DocumentSource` stores in-memory raw text with an id, title, source type, content, and metadata.
- `DocumentChunk` stores a deterministic chunk with source id, content, index, keywords, domains, and metadata.
- `TextChunker` splits text by character windows with overlap and practical word-boundary handling.
- `extract_keywords()` and `assign_domains()` use simple deterministic rules, not ML.
- `DocumentIngestor` converts `DocumentSource` values into chunks, chunks into `MemoryRecord` values, and sources into an `InMemoryKeywordMemory` module.
- `create_demo_document_sources()` provides small in-memory examples for car diagnostics, code review, cybersecurity, media workflow, and document indexing.

The path is:

```text
Raw document text -> DocumentSource -> DocumentChunk -> MemoryRecord -> InMemoryKeywordMemory -> ContextBuilder
```

This is in-memory deterministic text ingestion only. It does not parse PDFs, run OCR, crawl the filesystem, build embeddings, use a vector database, or call external APIs.

## Safety Policy Layer

The safety layer prepares Grona for future local tools without adding real tool execution yet.

- `ToolAction` describes a planned action such as `read_file`, `write_file`, `run_command`, `network_request`, `delete_file`, `modify_system`, or `unknown`.
- `PolicyDecision` explains whether that action is allowed, blocked, dry-run only, or requires confirmation.
- `SafetyPolicy` evaluates actions with conservative defaults.
- `ExecutionPlan` groups a request, planned actions, and policy decisions.
- `SafeExecutionAdapter` wraps an adapter, evaluates planned actions, and returns an `ExpertResult` explaining the safety outcome.
- `SafeToolRunner` evaluates a `ToolAdapter` plan before returning a deterministic `ToolResult`.

Dry-run means Grona produced and evaluated a plan. It does not mean any shell command, subprocess, external API, scanner, file processor, real filesystem tool, network operation, or sandboxed process ran.

## Tool Adapter Prototype

The tool adapter layer is intentionally small and safe:

- `ToolSpec` describes a mock tool name, action type, risk, read-only status, and metadata.
- `ToolRequest` describes a selected expert module asking for mock tool help.
- `ToolResult` returns deterministic mock output and includes `to_text()` for display.
- `MockToolAdapter` never touches files, networks, subprocesses, or external APIs.
- `ToolRegistry` supports registration, lookup, listing, action-type search, and metadata search.
- `create_default_tool_registry()` creates mock tools for code, car diagnostics, cybersecurity, media/video, and document search.

This is a boundary prototype for future tool use, not real tool use.

## Run Tests

```bash
pytest
```

Optional linting:

```bash
ruff check .
```

## Current Limitations

- Demo executors, adapters, and mock tool adapters are deterministic stubs, not real AI reasoning.
- Document ingestion is in-memory deterministic text ingestion only.
- The router and memory retrieval are keyword/domain based.
- No PDF parsing, OCR, semantic embeddings, vector search, or filesystem crawler is implemented.
- The safety layer is policy/planning only, not a real sandbox.
- No process isolation is implemented.
- No shell commands, subprocess execution, sandboxing, real filesystem tools, or unsafe tools are implemented.
- No external tools, network requests, or external APIs are called.
- No OpenAI API, Ollama integration, web server, vector database, SQL database, or external APIs.
- No learning, adaptive tool execution, or real memory graph yet.
- No production orchestration.

These limits are intentional. Grona is currently a research/prototype foundation for sparse modular AI architecture.
