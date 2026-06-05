# Changelog

## Unreleased

### Added

- Benchmark run persistence foundation for deterministic benchmark snapshots.
- `BenchmarkRunRecord`, `BenchmarkRunStore`, `InMemoryBenchmarkRunStore`, and `JsonlBenchmarkRunStore`.
- JSON-compatible serialization helpers for `BenchmarkResult` and `BenchmarkReport`.
- `BenchmarkRegressionReport` and `compare_benchmark_runs()` for candidate-vs-baseline score deltas.
- CLI `--benchmark-regression-demo` support through `python -m grona`.
- `examples/benchmark_regression_demo.py` and deterministic offline benchmark snapshot tests.
- Dataset quality review foundation for deterministic filtering before knowledge seed or training export use.
- `DatasetSampleReview`, `DatasetReviewConfig`, `DatasetQualityReviewer`, and `DatasetReviewReport`.
- Deterministic review checks for empty content, short samples, duplicates, missing answers, suspicious markers, unsupported shapes, license restrictions, low information density, and optional domain mismatch.
- Bridge from accepted reviewed dataset samples into raw `KnowledgeSeed` candidates with review metadata preserved.
- CLI `--dataset-review-demo` support through `python -m grona` using tiny in-memory JSONL only.
- `examples/dataset_review_demo.py` and deterministic offline dataset review tests.
- Dataset manifest and JSONL ingestion foundation for explicit local dataset provenance.
- `DatasetManifest`, `DatasetLicensePolicy`, `JsonlDatasetRecord`, `DatasetIngestor`, and `DatasetIngestionReport`.
- Deterministic JSONL text, stream, and explicit file parser helpers with line numbers.
- Manifest-aware normalization for Alpaca-like, ShareGPT-like, and generic text JSONL records.
- Conservative dataset license policy for knowledge seed and training export candidate uses.
- CLI `--jsonl-dataset-demo` support through `python -m grona` using tiny in-memory JSONL only.
- `examples/jsonl_dataset_ingestion_demo.py` and deterministic offline manifest/JSONL ingestion tests.
- TrainingDataExporter foundation for conservative in-memory training example candidates.
- `TrainingExample`, `TrainingDataset`, `TrainingExportConfig`, and `TrainingDataExporter`.
- Deterministic Grona-native JSONL and Alpaca-like JSONL string export helpers.
- Conservative export policy that skips raw and rejected records by default.
- Training export support for validated knowledge seeds, reviewed knowledge decisions, positive feedback records, and synthetic benchmark traces.
- CLI `--training-export-demo` support through `python -m grona`.
- `examples/training_export_demo.py` and deterministic offline training exporter tests.
- Donor model adapter foundation for untrusted proposal sources.
- `DonorModelProposal`, `DonorModelAdapter`, `StaticDonorModelAdapter`, and `LMStudioAdapter`.
- `DonorProposalCollector`, `DonorProposalBatch`, and explicit donor proposal error records.
- `knowledge_seed_from_donor_proposal()` bridge into raw untrusted Growth Lab seeds.
- CLI `--donor-demo` support through `python -m grona` using the deterministic static donor only.
- `examples/donor_model_demo.py` and deterministic offline donor adapter tests.
- Deterministic BenchmarkSuite MVP for local prototype comparisons.
- `BenchmarkCase`, `BenchmarkRunConfig`, `BenchmarkResult`, `BenchmarkReport`, and `BenchmarkSuite`.
- Deterministic scoring helpers for domain coverage, module coverage, context keyword coverage, growth trace relevance, routing score, and overall score.
- Demo benchmark cases for automotive cooling, cybersecurity/code review, media/video workflow, document retrieval, and general instruction following.
- Demo benchmark configs for baseline routing, orchestrated demo memory, and dataset-growth comparison.
- CLI `--benchmark-demo` support through `python -m grona`.
- `examples/benchmark_demo.py`.
- Benchmarking documentation and deterministic tests.
- Deterministic Dataset Ingestion Foundation for Growth Lab.
- `DatasetSource`, `DatasetSample`, `InstructionDatasetSample`, and `ConversationDatasetSample`.
- `AlpacaFormatAdapter` and `ShareGPTFormatAdapter` for tiny in-memory demo samples.
- `knowledge_seed_from_dataset_sample()` and `knowledge_seeds_from_dataset_samples()`.
- Demo dataset source and sample helpers for Alpaca-like, ShareGPT-like, and UA-Alpaca-like data.
- CLI `--dataset-demo` for dataset sample normalization into Growth Lab seeds.
- `examples/dataset_ingestion_demo.py`.
- Dataset ingestion documentation and deterministic tests.
- Deterministic GrowthEngine MVP for Growth Lab recommendations.
- `GrowthDecision`, `GrowthPlan`, `GrowthEngineConfig`, and `GrowthEngine`.
- `memory_records_from_growth_plan()` bridge from GrowthPlan decisions into memory records.
- Demo GrowthEngine seeds and `create_demo_growth_plan()` helper.
- CLI `--growth-engine-demo` for deterministic growth planning output.
- `examples/growth_engine_demo.py`.
- GrowthEngine deterministic tests and documentation updates.
- Growth Lab deterministic GrapeNode and GrapeCluster structures.
- `GrapeAssignment` traces and deterministic `GrapeClusterer` confidence scoring.
- `memory_records_from_grape_clusters()` bridge from reviewed clusters into memory records.
- CLI `--grape-demo` for deterministic Growth Lab cluster creation output.
- `examples/grape_cluster_demo.py`.
- Growth Lab deterministic KnowledgeSeed review pipeline.
- `NormalizedKnowledge`, `DuplicateCheckResult`, `ConflictCheckResult`, and `SeedReviewDecision`.
- `KnowledgeDeduplicator`, `KnowledgeConflictDetector`, and `KnowledgeReviewPipeline`.
- CLI `--growth-review-demo` for deterministic validation, duplicate, conflict, and review output.
- `examples/knowledge_review_demo.py`.
- Growth Lab KnowledgeSeed validation foundation.
- `KnowledgeSource`, `KnowledgeSeed`, `ValidationResult`, and `KnowledgeValidator`.
- Deterministic demo knowledge sources and seeds.
- Conversion helpers from `DocumentChunk` and `ToolResult` into raw knowledge seeds.
- CLI `--growth-demo` for deterministic seed validation output.
- `examples/knowledge_seed_demo.py`.
- Growth Lab documentation.
- Public project polish for the v0.1.0 prototype preparation pass.
- README landing-page structure with badges, architecture diagram, quickstart, feature map, and documentation links.
- Project vision document for Growth Lab, KnowledgeSeed, GrapeCluster, GrowthEngine, BenchmarkSuite, and related research directions.
- Future v0.1.0-prototype release notes.
- Contributing guide, security note, issue templates, and pull request template.
- Explicit MIT license file.

## v0.1.0-prototype

Planned first public prototype milestone. See `docs/release-notes-v0.1.0-prototype.md`.
