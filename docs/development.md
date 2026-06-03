# Development Notes

Grona is an early research prototype. Keep the code small, readable, deterministic, and honest about what it does.

## Repository Structure

```text
src/grona/
|-- adaptive.py      Feedback-informed score adjustment helpers
|-- adapters.py      ExecutionRequest, adapters, and adapter registry
|-- cli.py           Routing, orchestration, memory, ingestion, execution, safety, and tool CLI
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
`-- tools.py         ToolSpec, ToolRequest, ToolResult, ToolRegistry, SafeToolRunner
```

## Metadata vs Ingestion vs Execution vs Safety vs Tools

`ExpertModule` is metadata for routing. `DocumentSource` and `DocumentChunk` are in-memory ingestion data. `MemoryRecord` is retrievable context. `ExecutableExpert` is a direct runnable contract. `ExecutionAdapter` is a bridge from a selected module to a backend. `ToolAdapter` is a future-facing mock tool boundary. `SafetyPolicy` evaluates planned future tool actions before an adapter backend becomes real.

Keep them separate:

- metadata helps the router select modules
- ingestion turns raw text into deterministic chunks and memory records
- memory modules retrieve route-relevant context
- direct executors produce `ExpertResult` values from a task and context
- adapters normalize backend integration through `ExecutionRequest`
- tool adapters normalize mock tool integration through `ToolRequest` and `ToolResult`
- safety policy evaluates `ToolAction` plans without executing anything unsafe
- real tools, parsers, embeddings, or models can be added later without changing routing metadata

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
chunks = ingestor.ingest(source)
records = ingestor.chunks_to_memory_records(chunks)
```

To use documents as orchestration memory:

```python
memory = ingestor.build_memory_module("my-doc-memory", (source,))
```

This does not read paths, crawl folders, parse PDFs, run OCR, build embeddings, or call a vector database.

## Add an Execution Adapter

Use an adapter when you want a backend bridge instead of a direct executor:

```python
from grona import ExecutionRequest, ExpertResult, PythonFunctionAdapter

def handler(request: ExecutionRequest) -> ExpertResult:
    return ExpertResult(
        module_name=request.module_name,
        task=request.task,
        summary="Prepared a deterministic adapter result.",
        details=("No external tools were called.",),
        confidence=0.6,
    )

adapter = PythonFunctionAdapter(
    name="my-function-adapter",
    supported_modules=("my-module",),
    handler=handler,
)
```

## Add a Mock Tool Adapter

Use a tool adapter only for deterministic mock tool behavior right now:

```python
from grona import MockToolAdapter, ToolSpec

adapter = MockToolAdapter(
    ToolSpec(
        name="mock-my-tool",
        description="Returns a deterministic demo result.",
        action_type="read_file",
        risk_level="low",
        read_only=True,
        metadata={"domain": "docs"},
    )
)
```

Register it with `ToolRegistry`, or add it to `create_default_tool_registry()` if it is a useful default demo tool.

## Run Demo Execution

```bash
python -m grona "Diagnose engine overheating" --orchestrate --use-demo-memory
python -m grona "Diagnose engine overheating" --orchestrate --ingest-demo-docs
python -m grona "Review security logs" --orchestrate --use-demo-adapters --safe
python -m grona "Review code" --use-demo-adapters --dry-run-tools
python -m grona "Analyze engine overheating symptoms" --use-demo-tools
python examples/document_ingestion_demo.py
python examples/tool_adapter_demo.py
```

## Run Tests

```bash
pip install -e .[dev]
pytest
ruff check .
```

## What Not to Add Yet

Do not add these until the ingestion, execution, and safety interfaces have stronger tests and real requirements:

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
- real cybersecurity scanning
- real document or media processing
- hidden global memory
- claims that policy evaluation is real isolation
- claims that deterministic ingestion, demo executors, adapters, or mock tool adapters are real AI reasoning

The current ingestion, safety, and tool layers are deterministic planning foundations, not production execution, sandboxing, or RAG.
