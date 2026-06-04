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
- Growth Lab seed validation and deterministic review primitives
- Growth Lab grape node, grape cluster, assignment, and memory bridge primitives
- Growth Lab deterministic `GrowthEngine` recommendation MVP
- deterministic `BenchmarkSuite` MVP for routing, context, and growth trace scoring
- donor model proposal foundation with static offline proposals and optional LM Studio adapter scaffolding
- conservative `TrainingDataExporter` foundation for in-memory reviewed example candidates
- public README polish and project documentation
- examples, tests, and CI

## Dataset Manifest And JSONL Foundation

Goal: describe small local dataset sources explicitly and normalize supported JSONL records without hiding provenance, license, or review boundaries.

Current foundation:

- `DatasetManifest`
- `DatasetLicensePolicy`
- `DatasetPolicyDecision`
- `JsonlDatasetRecord`
- `DatasetIngestor`
- `DatasetIngestionReport`
- JSONL text, stream, and explicit file parser helpers
- manifest-aware Alpaca-like, ShareGPT-like, and generic text normalization
- policy decisions for knowledge seed candidates and training export candidates
- CLI `--jsonl-dataset-demo`
- `examples/jsonl_dataset_ingestion_demo.py`
- offline tests

Boundaries:

- no dataset downloads
- no Hugging Face integration
- no `datasets` dependency
- no pandas, pyarrow, fastparquet, or heavy dependencies
- no Parquet support yet
- no large dataset streaming
- no automatic training
- no automatic promotion to durable knowledge
- no trust in donor/model-generated data without review

Possible next work:

- persisted manifest files
- explicit safe file-writing/export paths
- larger JSONL streaming design
- Parquet reader design after storage requirements are clearer
- dataset manifest validation reports
- license policy presets and review workflows

## TrainingDataExporter Foundation

Goal: export reviewed and validated traces, feedback, benchmark examples, and knowledge seeds as explicit future training candidates without training anything.

Current foundation:

- `TrainingExample`
- `TrainingDataset`
- `TrainingExportConfig`
- `TrainingDataExporter`
- conservative default policy that skips raw and rejected records
- support for validated `KnowledgeSeed` values
- support for accepted review decisions
- support for positive feedback records
- support for synthetic benchmark traces
- deterministic Grona-native JSONL string export
- deterministic Alpaca-like JSONL string export
- CLI `--training-export-demo`
- `examples/training_export_demo.py`
- offline tests

Boundaries:

- no model training
- no LLM calls
- no LM Studio calls
- no dataset downloads
- no Hugging Face integration
- no Parquet export
- no JSONL file writing by default
- no claim that exported examples are high-quality real training data
- raw donor proposals are not exported by default

Possible next work:

- explicit file-writing export method with user-provided path
- persisted training export manifest
- stronger human review metadata
- benchmark impact checks before accepting exported datasets
- explicit license policy checks
- JSONL and Parquet reader designs after storage needs are clearer

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

## DonorModelAdapter / LMStudioAdapter Foundation

Goal: optionally use model outputs as untrusted proposal sources without making network calls part of the default prototype.

Current foundation:

- `DonorModelProposal`
- `DonorModelAdapter`
- `StaticDonorModelAdapter`
- optional `LMStudioAdapter` using only the Python standard library
- `DonorProposalCollector`
- `DonorProposalBatch`
- visible donor proposal error records
- `knowledge_seed_from_donor_proposal`
- CLI `--donor-demo`
- `examples/donor_model_demo.py`
- offline tests for static donor behavior and LM Studio adapter construction

Boundaries:

- static donor demos are deterministic and offline
- LM Studio is optional and must be explicitly configured by callers
- CI does not require LM Studio, external APIs, or network access
- donor output is untrusted until validation, review, benchmarks, and human judgment accept it
- this is not training, self-improvement, or automatic expert creation

Possible next work:

- persisted donor proposal records
- explicit runtime config for opt-in model-backed donor adapters
- benchmark impact checks for donor-derived context
- review workflow before donor proposals become durable knowledge
- adapter comparison reports that keep errors and provenance visible

## Dataset Ingestion Next Steps

Goal: prepare future dataset sources without losing provenance, license, or quality boundaries.

Possible next work:

- persisted dataset manifests
- sample filtering and review traces
- license policy checks before export or training use
- workspace relevance scoring for dataset samples
- deterministic dataset split metadata
- benchmark impact checks for dataset-derived context
- explicit Parquet reader design

Any future support for `yahma/alpaca-cleaned`, UA-Alpaca, OpenHermes, LMSYS / ShareGPT, Loghub, C4 slices, or Wikipedia-derived samples should keep downloads optional, provenance explicit, and tests small.

## BenchmarkSuite Next Steps

Goal: prepare Grona-vs-monolith experiments without hiding evaluation assumptions.

Possible next work:

- persisted benchmark run records
- richer deterministic rubrics
- route regression snapshots
- human review fields
- optional adapter output comparison
- future local LLM judge experiments behind explicit config
- future monolithic model adapter baselines
- benchmark impact checks before accepting GrowthEngine recommendations

BenchmarkSuite should keep reports explicit and conservative. It should not become an opaque automatic quality claim.

## Later Product Surfaces

UI/API layers should come after the architecture contracts are stable enough to display useful traces:

- active workspace profile
- selected modules and scores
- dataset manifest, policy, source, and sample provenance
- donor proposal source, type, validation status, and error status
- benchmark case and report summaries
- training export candidate counts, validation statuses, and provenance
- knowledge seed validation and review status
- grape cluster assignment status
- GrowthEngine decision status
- context sources
- expert results
- mock tool results
- safety decisions
- feedback signals
