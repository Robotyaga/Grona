# Development Notes

Grona is an early research prototype. Keep the code small, readable, deterministic, and honest about what it does.

See also [Contributing](../CONTRIBUTING.md), [Security](../SECURITY.md), [Architecture](architecture.md), [Growth Lab](growth-lab.md), [Dataset ingestion](dataset-ingestion.md), [Benchmarking](benchmarking.md), [Project vision](project-vision.md), and [Roadmap](roadmap.md).

## Repository Structure

```text
src/grona/
|-- adaptive.py                 Feedback-informed score adjustment helpers
|-- adapters.py                 ExecutionRequest, adapters, and adapter registry
|-- benchmark_cli.py            BenchmarkSuite CLI demo formatter
|-- benchmark_regression_cli.py Benchmark run snapshot regression CLI demo
|-- benchmark_runs.py           Run records, stores, serialization, regression reports
|-- benchmarks.py               BenchmarkCase, BenchmarkSuite, reports, scoring helpers
|-- cli.py                      Routing, workspace, memory, ingestion, execution, safety, tool, and growth CLI
|-- context.py                  ContextItem and ContextBuilder
|-- dataset_manifest.py         DatasetManifest, policy, JSONL records, DatasetIngestor
|-- dataset_review.py           DatasetSampleReview, DatasetQualityReviewer, review reports
|-- dataset_review_cli.py       Offline dataset quality review CLI demo
|-- datasets.py                 DatasetSource, DatasetSample, adapters, seed conversion
|-- decision.py                 Routing decision data structures
|-- defaults.py                 Default module registry
|-- documents.py                DocumentSource, TextChunker, DocumentIngestor
|-- donor.py                    Donor proposals, static donor, LM Studio adapter foundation
|-- donor_cli.py                Offline donor proposal CLI demo
|-- executor.py                 ExpertResult, ExecutableExpert, demo executors
|-- experiment_cli.py           Offline ExperimentRunner comparison CLI demo
|-- experiments.py              Experiment configs, runner, monolith stub, comparison report
|-- feedback.py                 Feedback records and route history stores
|-- growth.py                   KnowledgeSource, KnowledgeSeed, KnowledgeValidator
|-- growth_clusters.py          GrapeNode, GrapeCluster, assignments, and memory bridge
|-- growth_engine.py            GrowthDecision, GrowthPlan, GrowthEngine recommendations
|-- growth_review.py            KnowledgeSeed deduplication, conflict checks, and review decisions
|-- jsonl_dataset_cli.py        Offline JSONL dataset ingestion CLI demo
|-- memory.py                   MemoryRecord and deterministic keyword memory
|-- module.py                   ExpertModule routing metadata
|-- orchestrator.py             Orchestrator and OrchestrationResult
|-- registry.py                 ModuleRegistry
|-- router.py                   Keyword/domain router
|-- safety.py                   ToolAction, SafetyPolicy, ExecutionPlan, SafeExecutionAdapter
|-- tools.py                    ToolSpec, ToolRequest, ToolResult, ToolRegistry, SafeToolRunner
|-- training.py                 TrainingExample, TrainingDataset, TrainingDataExporter
|-- training_cli.py             Offline training export CLI demo
`-- workspace.py                WorkspaceProfile, WorkspaceConfig, built-in profiles
```

## Add Benchmark Cases

Use `BenchmarkCase` when a deterministic task should be tracked over time. Keep cases tiny, explicit, and stable. Do not add large benchmark datasets yet.

## Add Benchmark Configs

Use `BenchmarkRunConfig` to compare deterministic feature sets. Configs should describe local deterministic behavior only. They should not call model APIs, external services, downloads, embeddings, or training code.

## Persist Benchmark Runs

Use `BenchmarkRunRecord` when a report should become an explicit snapshot:

```python
from grona import BenchmarkSuite, create_benchmark_run_record, create_demo_benchmark_cases

suite = BenchmarkSuite(create_demo_benchmark_cases())
report = suite.run(config)
record = create_benchmark_run_record(
    report,
    "local-run-001",
    created_at="2026-01-01T00:00:00+00:00",
)
```

Use `InMemoryBenchmarkRunStore` for tests and demos. Use `JsonlBenchmarkRunStore` only when a caller explicitly provides a path for local JSONL persistence.

## Compare Benchmark Runs

Use `compare_benchmark_runs()` to compare a candidate snapshot against a baseline. Regression reports are deterministic score deltas only. They are not LLM judging, statistical proof, or real model accuracy claims.

## Add Experiment Configs

Use `ExperimentConfig` when multiple deterministic benchmark configurations should be compared in one report:

```python
from grona import ExperimentConfig

config = ExperimentConfig(
    "memory-context",
    "Grona routing with deterministic demo memory and orchestration.",
    "memory_context",
)
```

Supported modes are `routing_only`, `orchestrated_context`, `memory_context`, `growth_trace`, and `monolith_stub`.

## Run Experiments

Use `ExperimentRunner` to run configs side by side:

```python
from grona import ExperimentRunner, create_demo_benchmark_cases, create_demo_experiment_configs

runner = ExperimentRunner(
    create_demo_benchmark_cases(),
    create_demo_experiment_configs(),
    baseline_config_name="routing-only",
)
results, comparison = runner.run_and_compare()
print(comparison.to_text())
```

`ExperimentRunner` reuses `BenchmarkSuite`, `BenchmarkRunRecord`, and regression comparison helpers. `MonolithBaseline` is a deterministic stub only; do not treat it as a real monolithic LLM baseline.

## Run Benchmarks And Experiments

```bash
python -m grona --benchmark-demo
python -m grona --benchmark-regression-demo
python -m grona --experiment-demo
python examples/benchmark_demo.py
python examples/benchmark_regression_demo.py
python examples/experiment_comparison_demo.py
pytest tests/test_benchmarks.py tests/test_benchmark_runs.py tests/test_experiments.py
```

BenchmarkSuite measures expected domain coverage, module coverage, keyword/context coverage, and GrowthEngine trace relevance. The experiment layer compares those deterministic scores without changing the scoring logic.

## Add Dataset Manifests And JSONL Samples

Use `DatasetManifest` before parsing local JSONL rows so provenance, license, allowed uses, domains, capabilities, and review requirements stay explicit. Keep JSONL ingestion tiny, explicit, and deterministic. Do not add downloads, Hugging Face dependencies, large files, generated artifacts, training, embeddings, or vector databases at this layer.

## Review Normalized Dataset Samples

Use `DatasetQualityReviewer` after normalization and before creating raw `KnowledgeSeed` candidates. Dataset review is a deterministic quality gate, not an LLM judge, semantic deduplicator, legal review, training-data guarantee, or automatic promotion step.

## Add Donor Proposals

Use `StaticDonorModelAdapter` when tests or examples need deterministic donor output. A donor model is a proposal source only. Its output is not trusted memory, not a route decision, not automatic learning, and not training data.

`LMStudioAdapter` is an optional foundation for a future local LM Studio-compatible server. Do not use it in CI or default demos. It should only run behind explicit user configuration and should keep errors visible.

## Add Training Export Candidates

Use `TrainingDataExporter` only after records have enough validation or review metadata for a conservative export. It should prepare future training examples, not train a model. Default policy skips raw and rejected records.

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
python -m grona --benchmark-regression-demo
python -m grona --experiment-demo
python -m grona --training-export-demo
python examples/jsonl_dataset_ingestion_demo.py
python examples/dataset_review_demo.py
python examples/donor_model_demo.py
python examples/benchmark_demo.py
python examples/benchmark_regression_demo.py
python examples/experiment_comparison_demo.py
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

Do not add these until the workspace, ingestion, review, growth, donor, execution, benchmarking, experiments, training export, and safety interfaces have stronger tests and real requirements:

- dataset downloads
- Hugging Face `datasets` dependency
- real benchmark dataset downloads
- external judge models
- real monolithic LLM comparison claims
- LLM-based dataset, benchmark, or experiment judging
- semantic dataset deduplication
- real Alpaca, ShareGPT, OpenHermes, C4, Wikipedia, LMSYS, or Loghub downloads
- large dataset files or generated benchmark artifacts
- Parquet readers without a scoped design
- persisted workspace, seed, donor proposal, cluster, growth plan, or training dataset stores
- benchmark file writing by default
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

The current workspace, ingestion, review, donor, growth, benchmarking, benchmark snapshots, experiments, training export, safety, and tool layers are deterministic planning foundations, not production execution, sandboxing, RAG, truth verification, training, evaluation, or config management.
