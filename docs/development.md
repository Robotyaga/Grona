# Development Notes

Grona is an early research prototype. Keep the code small, readable, deterministic, and honest about what it does.

See also [Contributing](../CONTRIBUTING.md), [Security](../SECURITY.md), [Architecture](architecture.md), [Growth Lab](growth-lab.md), [Dataset ingestion](dataset-ingestion.md), [Project vision](project-vision.md), and [Roadmap](roadmap.md).

## Repository Structure

```text
src/grona/
|-- adaptive.py         Feedback-informed score adjustment helpers
|-- adapters.py         ExecutionRequest, adapters, and adapter registry
|-- cli.py              Routing, workspace, memory, ingestion, execution, safety, tool, and growth CLI
|-- context.py          ContextItem and ContextBuilder
|-- datasets.py         DatasetSource, DatasetSample, adapters, seed conversion
|-- decision.py         Routing decision data structures
|-- defaults.py         Default module registry
|-- documents.py        DocumentSource, TextChunker, DocumentIngestor
|-- executor.py         ExpertResult, ExecutableExpert, demo executors
|-- feedback.py         Feedback records and route history stores
|-- growth.py           KnowledgeSource, KnowledgeSeed, KnowledgeValidator
|-- growth_clusters.py  GrapeNode, GrapeCluster, assignments, and memory bridge
|-- growth_engine.py    GrowthDecision, GrowthPlan, GrowthEngine recommendations
|-- growth_review.py    KnowledgeSeed deduplication, conflict checks, and review decisions
|-- memory.py           MemoryRecord and deterministic keyword memory
|-- module.py           ExpertModule routing metadata
|-- orchestrator.py     Orchestrator and OrchestrationResult
|-- registry.py         ModuleRegistry
|-- router.py           Keyword/domain router
|-- safety.py           ToolAction, SafetyPolicy, ExecutionPlan, SafeExecutionAdapter
|-- tools.py            ToolSpec, ToolRequest, ToolResult, ToolRegistry, SafeToolRunner
`-- workspace.py        WorkspaceProfile, WorkspaceConfig, built-in profiles
```

## Metadata vs Workspace vs Ingestion vs Growth vs Execution

Keep concerns separate:

- workspace profiles choose active modules/domains and default behavior
- metadata helps the router select modules
- document ingestion turns raw text into deterministic chunks and memory records
- dataset ingestion normalizes tiny structured samples into Growth Lab seed material
- growth seeds represent raw knowledge before trust or promotion
- validation scores seeds without fact-checking, web access, or model calls
- deduplication marks repeated seeds as merge candidates without deleting provenance
- conflict detection marks potential contradictions without resolving truth
- review decisions recommend next steps before future memory or cluster promotion
- grape clustering groups only promote-candidate reviewed seeds into candidate structures
- GrowthEngine recommends next actions without mutating seeds, clusters, modules, or memory
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

## Add Dataset Samples

Use `DatasetSource` and format adapters when tiny structured dataset samples should enter Growth Lab:

```python
from grona import AlpacaFormatAdapter, DatasetSource

source = DatasetSource(
    "dataset:demo-alpaca",
    "Demo Alpaca",
    source_type="instruction_dataset",
    format="alpaca",
    license="cc-by-4.0",
    language="en",
    reliability=0.8,
)
records = [
    {
        "instruction": "Explain how to review a Python function.",
        "input": "A helper changed without tests.",
        "output": "Check behavior, edge cases, imports, and add focused tests.",
    }
]
samples = AlpacaFormatAdapter().parse(records, source)
```

Convert normalized samples into seeds before validation:

```python
from grona import knowledge_seeds_from_dataset_samples

normalized = [sample.to_dataset_sample() for sample in samples]
seeds = knowledge_seeds_from_dataset_samples(normalized)
```

Keep dataset ingestion in memory and deterministic. Do not add downloads, Hugging Face dependencies, large files, generated artifacts, training, embeddings, or vector databases at this layer.

## Add Knowledge Seeds

Use `KnowledgeSeed` for raw knowledge that still needs validation:

```python
from grona import KnowledgeSeed, KnowledgeSource, KnowledgeValidator

source = KnowledgeSource("source:notes", "user_note", "Project notes", reliability=0.8)
seed = KnowledgeSeed(
    id="seed:cooling-note",
    content="Engine overheating triage should check coolant, radiator flow, and fan activation.",
    source=source,
    domains=("automotive",),
    keywords=("engine", "overheating", "coolant"),
    confidence=0.75,
)
result = KnowledgeValidator().validate(seed)
```

Validation is deterministic scoring and warnings only. It is not truth verification, training, or promotion into trusted memory.

## Review Knowledge Seeds

Use `KnowledgeReviewPipeline` when seeds should be checked for duplicates and potential conflicts before future promotion:

```python
from grona import KnowledgeReviewPipeline

pipeline = KnowledgeReviewPipeline()
decisions = pipeline.review([seed])
```

Review decisions are recommendations only. They do not mutate modules, memory, clusters, tools, or model weights.

## Build Grape Clusters

Use `GrapeClusterer` after review decisions when promote-candidate seeds should become visible candidate clusters:

```python
from grona import GrapeClusterer, memory_records_from_grape_clusters

clusters, assignments = GrapeClusterer().cluster([seed], decisions)
records = memory_records_from_grape_clusters(clusters)
```

The clusterer is deterministic domain and keyword-overlap grouping. It is not embeddings, semantic clustering, autonomous growth, or training. Keep assignment reasons visible so skipped seeds remain auditable.

## Plan Growth Decisions

Use `GrowthEngine` after review and clustering when Grona should recommend next actions:

```python
from grona import GrowthEngine, memory_records_from_growth_plan

plan = GrowthEngine().plan_growth([seed], decisions, clusters, assignments)
records = memory_records_from_growth_plan(plan, clusters)
```

`GrowthEngine` may recommend seed promotion, duplicate merge, quarantine, rejection, candidate cluster creation, cluster strengthening, memory-record preparation, cluster review, or expert-candidate proposals.

It must remain a recommendation layer. Do not make it silently mutate modules, memory stores, clusters, tools, routing metadata, training data, or model weights.

## Run Demo Execution

```bash
python -m grona "Diagnose engine overheating" --workspace automotive
python -m grona "Review this Python script for security issues" --workspace cybersecurity
python -m grona "Plan MotionCam RAW workflow" --workspace media
python -m grona "Diagnose engine overheating" --orchestrate --ingest-demo-docs
python -m grona --growth-demo
python -m grona --growth-review-demo
python -m grona --grape-demo
python -m grona --growth-engine-demo
python -m grona --dataset-demo
python examples/workspace_profile_demo.py
python examples/knowledge_seed_demo.py
python examples/knowledge_review_demo.py
python examples/grape_cluster_demo.py
python examples/growth_engine_demo.py
python examples/dataset_ingestion_demo.py
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

Do not add these until the workspace, ingestion, growth, execution, and safety interfaces have stronger tests and real requirements:

- dataset downloads
- Hugging Face `datasets` dependency
- real Alpaca, ShareGPT, OpenHermes, C4, Wikipedia, LMSYS, or Loghub downloads
- large dataset files or generated dataset artifacts
- JSONL or Parquet readers without a scoped design
- persisted workspace directories
- persisted seed stores
- persisted cluster stores
- persisted growth plan stores
- external config files loaded from disk
- secrets or credential handling
- production config management
- OpenAI API calls
- Ollama integration
- donor model adapters
- external APIs
- web servers
- vector databases
- SQL databases
- production task queues
- filesystem crawling
- PDF parsing dependencies
- OCR
- embeddings or semantic search
- LLM-based contradiction detection
- external evidence lookup
- automatic truth resolution
- subprocess or shell execution
- real filesystem tool execution
- network tool execution
- sandboxing claims
- automatic expert growth
- automatic model training
- model weights

The current workspace, ingestion, growth, safety, and tool layers are deterministic planning foundations, not production execution, sandboxing, RAG, truth verification, training, or config management.
