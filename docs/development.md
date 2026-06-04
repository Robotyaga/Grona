# Development Notes

Grona is an early research prototype. Keep the code small, readable, deterministic, and honest about what it does.

See also [Contributing](../CONTRIBUTING.md), [Security](../SECURITY.md), [Architecture](architecture.md), [Growth Lab](growth-lab.md), [Dataset ingestion](dataset-ingestion.md), [Benchmarking](benchmarking.md), [Project vision](project-vision.md), and [Roadmap](roadmap.md).

## Repository Structure

```text
src/grona/
|-- adaptive.py            Feedback-informed score adjustment helpers
|-- adapters.py            ExecutionRequest, adapters, and adapter registry
|-- benchmark_cli.py       BenchmarkSuite CLI demo formatter
|-- benchmarks.py          BenchmarkCase, BenchmarkSuite, reports, scoring helpers
|-- cli.py                 Routing, workspace, memory, ingestion, execution, safety, tool, and growth CLI
|-- context.py             ContextItem and ContextBuilder
|-- dataset_manifest.py    DatasetManifest, policy, JSONL records, DatasetIngestor
|-- dataset_review.py      DatasetSampleReview, DatasetQualityReviewer, review reports
|-- dataset_review_cli.py  Offline dataset quality review CLI demo
|-- datasets.py            DatasetSource, DatasetSample, adapters, seed conversion
|-- decision.py            Routing decision data structures
|-- defaults.py            Default module registry
|-- documents.py           DocumentSource, TextChunker, DocumentIngestor
|-- donor.py               Donor proposals, static donor, LM Studio adapter foundation
|-- donor_cli.py           Offline donor proposal CLI demo
|-- executor.py            ExpertResult, ExecutableExpert, demo executors
|-- feedback.py            Feedback records and route history stores
|-- growth.py              KnowledgeSource, KnowledgeSeed, KnowledgeValidator
|-- growth_clusters.py     GrapeNode, GrapeCluster, assignments, and memory bridge
|-- growth_engine.py       GrowthDecision, GrowthPlan, GrowthEngine recommendations
|-- growth_review.py       KnowledgeSeed deduplication, conflict checks, and review decisions
|-- jsonl_dataset_cli.py   Offline JSONL dataset ingestion CLI demo
|-- memory.py              MemoryRecord and deterministic keyword memory
|-- module.py              ExpertModule routing metadata
|-- orchestrator.py        Orchestrator and OrchestrationResult
|-- registry.py            ModuleRegistry
|-- router.py              Keyword/domain router
|-- safety.py              ToolAction, SafetyPolicy, ExecutionPlan, SafeExecutionAdapter
|-- tools.py               ToolSpec, ToolRequest, ToolResult, ToolRegistry, SafeToolRunner
|-- training.py            TrainingExample, TrainingDataset, TrainingDataExporter
|-- training_cli.py        Offline training export CLI demo
`-- workspace.py           WorkspaceProfile, WorkspaceConfig, built-in profiles
```

## Add Dataset Manifests And JSONL Samples

Use `DatasetManifest` before parsing local JSONL rows so provenance, license, allowed uses, domains, capabilities, and review requirements stay explicit:

```python
from grona import DatasetIngestor, DatasetManifest

manifest = DatasetManifest(
    "demo-jsonl",
    "Small explicit JSONL corpus.",
    "in-memory-demo",
    license="MIT",
    allowed_uses=("knowledge_seed_candidate",),
    requires_review=True,
)

samples, report = DatasetIngestor().ingest_jsonl_text(
    manifest,
    '{"text":"Keep provenance visible before trust."}',
)
```

Keep JSONL ingestion tiny, explicit, and deterministic. Do not add downloads, Hugging Face dependencies, large files, generated artifacts, training, embeddings, or vector databases at this layer.

## Review Normalized Dataset Samples

Use `DatasetQualityReviewer` after normalization and before creating raw `KnowledgeSeed` candidates:

```python
from grona import DatasetQualityReviewer

reviewer = DatasetQualityReviewer()
reviews, review_report = reviewer.review_samples(samples, manifest)
seeds = reviewer.accepted_knowledge_seed_candidates(samples, reviews)
```

Dataset review is a deterministic quality gate. It can check empty content, short content, duplicate normalized text, missing answers, suspicious prompt markers, license restrictions, optional domain mismatch, and low information density. It is not an LLM judge, semantic deduplicator, legal review, training-data guarantee, or automatic promotion step.

## Add Donor Proposals

Use `StaticDonorModelAdapter` when tests or examples need deterministic donor output:

```python
from grona import DonorProposalCollector, StaticDonorModelAdapter

collector = DonorProposalCollector((StaticDonorModelAdapter(),))
batch = collector.collect("Summarize modular AI routing", ("summary", "knowledge_seed"))
```

A donor model is a proposal source only. Its output is not trusted memory, not a route decision, not automatic learning, and not training data. If a `knowledge_seed` proposal should enter Growth Lab, convert it into a raw seed and then validate/review it:

```python
from grona import knowledge_seed_from_donor_proposal

proposal = batch.proposals[-1]
seed = knowledge_seed_from_donor_proposal(proposal)
```

`LMStudioAdapter` is an optional foundation for a future local LM Studio-compatible server. Do not use it in CI or default demos. It should only run behind explicit user configuration and should keep errors visible.

## Add Training Export Candidates

Use `TrainingDataExporter` only after records have enough validation or review metadata for a conservative export. It should prepare future training examples, not train a model:

```python
from grona import TrainingDataExporter

exporter = TrainingDataExporter()
examples = exporter.from_knowledge_seeds(validated_seeds)
dataset = exporter.build_dataset(
    "reviewed-knowledge",
    "Reviewed knowledge candidates for future training experiments.",
    examples,
)
print(dataset.to_native_jsonl())
```

Default policy skips raw and rejected records. Raw donor proposals should not be exported directly. If donor material should become exportable, first convert it into a `KnowledgeSeed`, run validation/review, and export only the reviewed or validated result.

## Add Benchmark Cases

Use `BenchmarkCase` when a deterministic task should be tracked over time:

```python
from grona import BenchmarkCase

case = BenchmarkCase(
    "auto-overheating",
    "Diagnose engine overheating in traffic.",
    expected_domains=("automotive",),
    expected_modules=("automotive-diagnostics",),
    expected_keywords=("engine", "overheating", "coolant"),
    workspace="automotive",
)
```

Keep cases tiny, explicit, and stable. Do not add large benchmark datasets yet.

## Add Benchmark Configs

Use `BenchmarkRunConfig` to compare deterministic feature sets:

```python
from grona import BenchmarkRunConfig

config = BenchmarkRunConfig(
    "dataset-growth-demo",
    use_memory=True,
    use_demo_memory=True,
    use_dataset_seeds=True,
    use_grape_clusters=True,
    use_growth_engine=True,
    use_orchestrator=True,
)
```

Configs should describe local deterministic behavior only. They should not call model APIs, external services, downloads, embeddings, or training code.

## Run Benchmarks

```bash
python -m grona --benchmark-demo
python examples/benchmark_demo.py
pytest tests/test_benchmarks.py
```

BenchmarkSuite measures expected domain coverage, module coverage, keyword/context coverage, and GrowthEngine trace relevance. It is not a judge model and does not claim real answer accuracy.

## Add Dataset Samples

Use `DatasetSource` and format adapters when tiny structured dataset samples should enter Growth Lab. Keep dataset ingestion in memory and deterministic. Do not add downloads, Hugging Face dependencies, large files, generated artifacts, training, embeddings, or vector databases at this layer.

## Add Knowledge Seeds

Use `KnowledgeSeed` for raw knowledge that still needs validation. Validation is deterministic scoring and warnings only. It is not truth verification, training, or promotion into trusted memory.

## Plan Growth Decisions

Use `GrowthEngine` after review and clustering when Grona should recommend next actions. It must remain a recommendation layer and must not silently mutate modules, memory stores, clusters, tools, routing metadata, training data, or model weights.

## Run Demo Execution

```bash
python -m grona "Diagnose engine overheating" --workspace automotive
python -m grona "Review this Python script for security issues" --workspace cybersecurity
python -m grona --growth-demo
python -m grona --growth-review-demo
python -m grona --grape-demo
python -m grona --growth-engine-demo
python -m grona --dataset-demo
python -m grona --jsonl-dataset-demo
python -m grona --dataset-review-demo
python -m grona --donor-demo
python -m grona --benchmark-demo
python -m grona --training-export-demo
python examples/jsonl_dataset_ingestion_demo.py
python examples/dataset_review_demo.py
python examples/donor_model_demo.py
python examples/benchmark_demo.py
python examples/training_export_demo.py
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

Do not add these until the workspace, ingestion, review, growth, donor, execution, benchmarking, training export, and safety interfaces have stronger tests and real requirements:

- dataset downloads
- Hugging Face `datasets` dependency
- real benchmark dataset downloads
- external judge models
- LLM-based dataset judging
- semantic dataset deduplication
- real Alpaca, ShareGPT, OpenHermes, C4, Wikipedia, LMSYS, or Loghub downloads
- large dataset files or generated benchmark artifacts
- Parquet readers without a scoped design
- persisted workspace, seed, donor proposal, cluster, growth plan, benchmark, or training dataset stores
- external config files loaded from disk
- secrets or credential handling
- OpenAI API calls
- Ollama integration
- external APIs
- web servers
- vector databases
- SQL databases
- filesystem crawling
- PDF parsing dependencies
- OCR
- embeddings or semantic search
- LLM-based contradiction detection
- external evidence lookup
- automatic truth resolution
- subprocess or shell execution
- real filesystem tool execution
- network tool execution beyond explicit optional local-model adapter calls
- sandboxing claims
- automatic expert growth
- automatic model training
- model weights
- file-writing training export CLI by default
- claims that exported examples are already high-quality training data

The current workspace, ingestion, review, donor, growth, benchmarking, training export, safety, and tool layers are deterministic planning foundations, not production execution, sandboxing, RAG, truth verification, training, evaluation, or config management.
