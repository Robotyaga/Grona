# Development Notes

Grona is an early research prototype. Keep the code small, readable, deterministic, and honest about what it does.

See also [Contributing](../CONTRIBUTING.md), [Security](../SECURITY.md), [Architecture](architecture.md), [Project vision](project-vision.md), and [Roadmap](roadmap.md).

## Repository Structure

```text
src/grona/
|-- adaptive.py      Feedback-informed score adjustment helpers
|-- adapters.py      ExecutionRequest, adapters, and adapter registry
|-- cli.py           Routing, workspace, memory, ingestion, execution, safety, and tool CLI
|-- context.py       ContextItem and ContextBuilder
|-- decision.py      Routing decision data structures
|-- defaults.py      Default module registry
|-- documents.py     DocumentSource, TextChunker, DocumentIngestor
|-- executor.py      ExpertResult, ExecutableExpert, demo executors
|-- feedback.py      Feedback records and route history stores
|-- memory.py        MemoryRecord and deterministic keyword memory
|-- module.py        ExpertModule routing metadata
|-- orchestrator.py  Orchestrator and OrchestrationResult
|-- registry.py      ModuleRegistry
|-- router.py        Keyword/domain router
|-- safety.py        ToolAction, SafetyPolicy, ExecutionPlan, SafeExecutionAdapter
|-- tools.py         ToolSpec, ToolRequest, ToolResult, ToolRegistry, SafeToolRunner
`-- workspace.py     WorkspaceProfile, WorkspaceConfig, built-in profiles
```

## Metadata vs Workspace vs Ingestion vs Execution

Keep concerns separate:

- workspace profiles choose active modules/domains and default behavior
- metadata helps the router select modules
- ingestion turns raw text into deterministic chunks and memory records
- memory modules retrieve route-relevant context
- direct executors produce `ExpertResult` values from a task and context
- adapters normalize backend integration through `ExecutionRequest`
- tool adapters normalize mock tool integration through `ToolRequest` and `ToolResult`
- safety policy evaluates `ToolAction` plans without executing anything unsafe

## Add a Workspace Profile

Use `WorkspaceProfile` for a lightweight built-in or in-memory project profile:

```python
from grona import WorkspaceProfile

profile = WorkspaceProfile(
    name="my-profile",
    description="Focused project profile.",
    enabled_domains=("code", "documents", "general"),
    memory_sources=("project_notes",),
    tool_profiles=("mock_code_inspector",),
    routing_mode="adaptive",
    adaptive_enabled=True,
)
```

Filter modules without mutating the original registry:

```python
from grona import create_default_registry, filter_modules_for_workspace

registry = filter_modules_for_workspace(create_default_registry(), profile)
```

## Add In-Memory Documents

Use `DocumentSource` for text that is already available in memory:

```python
from grona import DocumentIngestor, DocumentSource, TextChunker

source = DocumentSource(
    id="my-note",
    title="My note",
    source_type="note",
    content="Check coolant, radiator flow, thermostat behavior, and fan activation.",
)

ingestor = DocumentIngestor(TextChunker(max_chars=200, overlap_chars=25))
records = ingestor.chunks_to_memory_records(ingestor.ingest(source))
```

This does not read paths, crawl folders, parse PDFs, run OCR, build embeddings, or call a vector database.

## Run Demo Execution

```bash
python -m grona "Diagnose engine overheating" --workspace automotive
python -m grona "Review this Python script for security issues" --workspace cybersecurity
python -m grona "Plan MotionCam RAW workflow" --workspace media
python -m grona "Diagnose engine overheating" --orchestrate --ingest-demo-docs
python examples/workspace_profile_demo.py
```

## Run Tests

```bash
pip install -e .[dev]
pytest
ruff check .
```

## Public Project Hygiene

Before opening a PR, check that the change:

- keeps prototype claims honest
- does not add heavy dependencies without discussion
- does not introduce real tool execution by accident
- keeps examples deterministic
- updates docs when public behavior changes
- includes tests for code changes

## What Not to Add Yet

Do not add these until the workspace, ingestion, execution, and safety interfaces have stronger tests and real requirements:

- persisted workspace directories
- external config files loaded from disk
- secrets or credential handling
- production config management
- OpenAI API calls
- Ollama integration
- external APIs
- web servers
- vector databases
- SQL databases
- production task queues
- filesystem crawling
- PDF parsing dependencies
- OCR
- embeddings or semantic search
- subprocess or shell execution
- real filesystem tool execution
- network tool execution
- sandboxing claims

The current workspace, ingestion, safety, and tool layers are deterministic planning foundations, not production execution, sandboxing, RAG, or config management.
