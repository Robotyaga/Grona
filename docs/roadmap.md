# Roadmap

Grona should stay readable before adding heavier infrastructure. The roadmap is intentionally staged so public polish, tests, safety boundaries, benchmarks, and research questions stay ahead of larger integrations.

## Documentation Map

- [Project vision](project-vision.md)
- [Architecture](architecture.md)
- [Growth Lab](growth-lab.md)
- [Dataset ingestion](dataset-ingestion.md)
- [Benchmarking](benchmarking.md)
- [Workspace profiles](workspaces.md)
- [Research notes](research-notes.md)
- [v0.1.0 prototype release notes](release-notes-v0.1.0-prototype.md)

## Completed Prototype Foundation

The repository already has the first deterministic foundation:

- `ExpertModule`, `ModuleRegistry`, `Router`, and `RoutingDecision`
- feedback records and adaptive routing
- memory modules and keyword memory
- in-memory document ingestion
- `ContextBuilder`, `Orchestrator`, and `OrchestrationResult`
- deterministic expert executors
- execution adapters
- safety policy planning
- mock tool adapters and safe mock runner
- workspace profiles and workspace-aware CLI
- Growth Lab dataset ingestion foundation for tiny in-memory samples
- dataset manifest and JSONL ingestion foundation with conservative license policy
- dataset quality review foundation for deterministic filtering before seed use
- Growth Lab seed validation and deterministic review primitives
- Growth Lab grape node, grape cluster, assignment, and memory bridge primitives
- Growth Lab deterministic `GrowthEngine` recommendation MVP
- deterministic `BenchmarkSuite` MVP for routing, context, and growth trace scoring
- benchmark run snapshot persistence and regression comparison foundation
- donor model proposal foundation with static offline proposals and optional LM Studio adapter scaffolding
- conservative `TrainingDataExporter` foundation for in-memory reviewed example candidates
- public README polish and project documentation
- examples, tests, and CI

## BenchmarkSuite MVP

Goal: make route quality and orchestration behavior measurable without model calls.

Current foundation:

- `BenchmarkCase`
- `BenchmarkRunConfig`
- `BenchmarkResult`
- `BenchmarkReport`
- `BenchmarkSuite`
- deterministic scoring helpers for domains, modules, context keywords, growth traces, and overall score
- demo benchmark cases for automotive, cybersecurity/code review, media/video, document retrieval, and general instruction following
- demo benchmark configs for baseline routing, orchestrated demo memory, and dataset-growth demo
- CLI `--benchmark-demo`
- `examples/benchmark_demo.py`
- deterministic tests

This layer is a rubric and reporting layer only. It does not call real LLMs, use LM Studio, call external APIs, download benchmark datasets, use embeddings, train models, or claim real answer accuracy.

## Benchmark Run Persistence And Regression Snapshots

Goal: keep benchmark runs comparable over time without introducing databases, services, model judges, or hidden state.

Current foundation:

- `BenchmarkRunRecord`
- `BenchmarkRunStore`
- `InMemoryBenchmarkRunStore`
- `JsonlBenchmarkRunStore`
- report/result dict and JSON serialization helpers
- `BenchmarkRegressionReport`
- `compare_benchmark_runs()`
- CLI `--benchmark-regression-demo`
- `examples/benchmark_regression_demo.py`
- offline tests

Boundaries:

- no LLM judging
- no statistical significance claims
- no CI gate yet
- no database or web server
- no file writes by default; JSONL persistence only happens when a caller gives a path
- no external APIs, downloads, embeddings, training, or datasets

Possible next work:

- explicit baseline files under user-provided paths
- CI-friendly regression thresholds
- persisted benchmark metadata for branch, commit, and suite version
- richer deterministic rubrics
- human review fields
- optional adapter output comparison
- future local LLM judge experiments behind explicit config
- future monolithic model adapter baselines
- benchmark impact checks before accepting GrowthEngine recommendations

## Dataset Manifest, JSONL, And Quality Review Foundation

Goal: describe small local dataset sources explicitly, normalize supported JSONL records, and filter normalized samples without hiding provenance, license, or review boundaries.

Current foundation includes `DatasetManifest`, `DatasetLicensePolicy`, `JsonlDatasetRecord`, `DatasetIngestor`, `DatasetQualityReviewer`, deterministic review reports, manifest-aware Alpaca-like and ShareGPT-like normalization, and CLI demos.

Boundaries: no downloads, Hugging Face dependency, heavy readers, embeddings, semantic deduplication, LLM judging, automatic training, or automatic promotion to durable knowledge.

## TrainingDataExporter Foundation

Goal: export reviewed and validated traces, feedback, benchmark examples, and knowledge seeds as explicit future training candidates without training anything.

Current foundation includes `TrainingExample`, `TrainingDataset`, `TrainingExportConfig`, `TrainingDataExporter`, conservative default export policy, native JSONL strings, Alpaca-like JSONL strings, CLI demo, example, and tests.

Boundaries: no model training, model calls, downloads, Parquet export, file writing by default, or claim that exported examples are high-quality real training data.

## DonorModelAdapter / LMStudioAdapter Foundation

Goal: optionally use model outputs as untrusted proposal sources without making network calls part of the default prototype.

Current foundation includes deterministic static donor proposals, optional `LMStudioAdapter` construction, visible donor errors, and a bridge from `knowledge_seed` proposals into raw untrusted Growth Lab seeds.

Boundaries: static donor demos are deterministic and offline; LM Studio is optional and must be explicitly configured; donor output is untrusted until validation, review, benchmarks, and human judgment accept it.

## Later Product Surfaces

UI/API layers should come after the architecture contracts are stable enough to display useful traces:

- active workspace profile
- selected modules and scores
- dataset manifest, policy, source, sample provenance, and quality review decision
- donor proposal source, type, validation status, and error status
- benchmark case, run snapshot, and regression report summaries
- training export candidate counts, validation statuses, and provenance
- knowledge seed validation and review status
- grape cluster assignment status
- GrowthEngine decision status
- context sources
- expert results
- mock tool results
- safety decisions
- feedback signals
