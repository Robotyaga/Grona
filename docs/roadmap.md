# Roadmap

Grona should stay readable before adding heavier infrastructure. The roadmap is intentionally staged so public polish, tests, safety boundaries, benchmarks, experiments, prompt provenance, and research questions stay ahead of larger integrations.

## Documentation Map

- [Project vision](project-vision.md)
- [Architecture](architecture.md)
- [Growth Lab](growth-lab.md)
- [Dataset ingestion](dataset-ingestion.md)
- [Benchmarking](benchmarking.md)
- [Prompting and inference traces](prompting.md)
- [Dry-run trainer interface](training-dry-run.md)
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
- `PromptTemplate`, `PromptBuilder`, `RenderedPrompt`, and `InferenceTrace`
- in-memory and explicit JSONL inference trace stores
- deterministic prompt trace demo through `StaticLocalLLMAdapter`
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
- `ExperimentRunner` foundation for deterministic Grona-vs-monolith comparison reports
- `ExperimentRegressionGate` foundation for warning-only threshold reports
- donor model proposal foundation with static offline proposals and optional LM Studio adapter scaffolding
- local LLM baseline adapter foundation with deterministic static demo and optional explicit LM Studio-compatible adapter
- conservative `TrainingDataExporter` foundation for in-memory reviewed example candidates
- training dataset package, config-only training plan, artifact bundle, and dry-run trainer preview foundations
- public README polish and project documentation
- examples, tests, and CI

## PromptTemplate And InferenceTrace Foundation

Goal: make model-facing prompt construction and adapter responses reproducible before real local LLM experiments or training-data workflows are added.

Current foundation includes `PromptTemplate`, `RenderedPrompt`, `PromptBuilder`, `InferenceTrace`, `InMemoryInferenceTraceStore`, `JsonlInferenceTraceStore`, default prompt templates, a deterministic static prompt trace runner, CLI `--prompt-trace-demo`, example, tests, and documentation.

Boundaries:

- no real model calls by default
- no LM Studio calls in tests or CI
- no external APIs
- no downloads, embeddings, training, database, or web server
- no automatic prompt optimization
- no answer quality judgment
- no automatic conversion of traces into training examples
- JSONL trace persistence only happens when a caller gives a path

Possible next work:

- explicit trace review decisions before training export
- task-output rubric records attached to traces
- opt-in local LM Studio trace runner after prompt contracts stabilize
- trace comparison reports that preserve prompt, response, routing, and context provenance

## BenchmarkSuite MVP

Goal: make route quality and orchestration behavior measurable without model calls.

Current foundation includes `BenchmarkCase`, `BenchmarkRunConfig`, `BenchmarkResult`, `BenchmarkReport`, `BenchmarkSuite`, deterministic scoring helpers, demo cases, demo configs, CLI demo, example, and tests.

This layer is a rubric and reporting layer only. It does not call real LLMs, use LM Studio, call external APIs, download benchmark datasets, use embeddings, train models, or claim real answer accuracy.

## Benchmark Run Persistence And Regression Snapshots

Goal: keep benchmark runs comparable over time without introducing databases, services, model judges, or hidden state.

Current foundation includes `BenchmarkRunRecord`, `BenchmarkRunStore`, `InMemoryBenchmarkRunStore`, `JsonlBenchmarkRunStore`, serialization helpers, `BenchmarkRegressionReport`, `compare_benchmark_runs()`, CLI demo, example, and tests.

Boundaries:

- no LLM judging
- no statistical significance claims
- no database or web server
- no file writes by default; JSONL persistence only happens when a caller gives a path
- no external APIs, downloads, embeddings, training, or datasets

## ExperimentRunner And Regression Gate Foundation

Goal: compare multiple deterministic configurations in one report and prepare future Grona-vs-monolith experiments plus CI-friendly threshold reports.

Current foundation:

- `ExperimentConfig`
- `ExperimentResult`
- `ExperimentRunner`
- `ExperimentComparisonReport`
- `ExperimentGateConfig`
- `ExperimentGateDecision`
- `ExperimentRegressionGate`
- `MonolithBaseline` deterministic stub
- demo experiment configs for routing-only, memory-context, growth-trace, and monolith-stub
- local LLM baseline experiment mode behind explicit adapter configuration
- CLI `--experiment-demo`
- CLI `--experiment-gate-demo`
- `examples/experiment_comparison_demo.py`
- `examples/experiment_gate_demo.py`
- offline tests

Boundaries:

- no real monolithic LLM baseline
- no LM Studio calls by default
- no external APIs
- no model judging
- no datasets, downloads, embeddings, training, database, or web server
- no statistical significance claims
- no claim that Grona is better than a monolithic AI system
- no default CI failure from experiment gate scores

Possible next work:

- explicit baseline selection files under user-provided paths
- CI-friendly gate command that remains opt-in
- local LLM baseline adapter behind explicit config
- reviewed inference traces before task output quality comparisons
- human review fields for task output quality
- task output rubrics after answer-producing adapters exist
- adapter comparison reports that preserve provenance and failures

## Dataset Manifest, JSONL, And Quality Review Foundation

Goal: describe small local dataset sources explicitly, normalize supported JSONL records, and filter normalized samples without hiding provenance, license, or review boundaries.

Current foundation includes `DatasetManifest`, `DatasetLicensePolicy`, `JsonlDatasetRecord`, `DatasetIngestor`, `DatasetQualityReviewer`, deterministic review reports, manifest-aware Alpaca-like and ShareGPT-like normalization, and CLI demos.

Boundaries: no downloads, Hugging Face dependency, heavy readers, embeddings, semantic deduplication, LLM judging, automatic training, or automatic promotion to durable knowledge.

## TrainingDataExporter Foundation

Goal: export reviewed and validated traces, feedback, benchmark examples, and knowledge seeds as explicit future training candidates without training anything.

Current foundation includes `TrainingExample`, `TrainingDataset`, `TrainingExportConfig`, `TrainingDataExporter`, conservative default export policy, native JSONL strings, Alpaca-like JSONL strings, CLI demo, example, and tests.

`InferenceTrace` records prompt/response provenance, but it is not automatically a training example. Future trace-to-training workflows should require explicit review policy and provenance checks before using traces as export candidates.

Boundaries: no model training, model calls, downloads, Parquet export, file writing by default, or claim that exported examples are high-quality real training data.

## Training Package, Artifact, And Dry-run Foundation

Goal: make future training inputs reviewable before any real trainer exists.

Current foundation includes deterministic `TrainingDatasetPackage` splits, `TrainingPlan` config validation, `TrainingArtifactBundle` assembly, conservative artifact writing with dry-run defaults, `TrainerBackendSpec`, `DryRunTrainerConfig`, `TrainingReadinessReport`, `TrainingExecutionPlan`, placeholder backend presets, CLI `--training-dry-run-demo`, example, tests, and documentation.

Boundaries: no actual training, subprocess execution, shell execution, environment probing, heavy training dependencies, model loading, downloads, uploads, GPU detection, or guarantee that command previews are runnable.

## DonorModelAdapter / LMStudioAdapter Foundation

Goal: optionally use model outputs as untrusted proposal sources without making network calls part of the default prototype.

Current foundation includes deterministic static donor proposals, optional `LMStudioAdapter` construction, visible donor errors, and a bridge from `knowledge_seed` proposals into raw untrusted Growth Lab seeds.

Boundaries: static donor demos are deterministic and offline; LM Studio is optional and must be explicitly configured; donor output is untrusted until validation, review, benchmarks, and human judgment accept it.

## Later Product Surfaces

UI/API layers should come after the architecture contracts are stable enough to display useful traces:

- active workspace profile
- selected modules and scores
- prompt template, rendered prompt, adapter response, and inference trace status
- dataset manifest, policy, source, sample provenance, and quality review decision
- donor proposal source, type, validation status, and error status
- benchmark case, run snapshot, regression report, experiment comparison, and gate decision summaries
- training export candidate counts, validation statuses, provenance, artifact readiness, and dry-run execution blockers
- knowledge seed validation and review status
- grape cluster assignment status
- GrowthEngine decision status
- context sources
- expert results
- mock tool results
- safety decisions
- feedback signals
