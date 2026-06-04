# Growth Lab

Growth Lab is the research foundation for future self-growing modular intelligence in Grona.

The long-term idea is:

```text
DatasetManifest -> DatasetLicensePolicy -> DatasetSample -> KnowledgeSeed -> validation
DonorModelProposal -> KnowledgeSeed -> validation
-> deduplication/conflict checks -> review decision -> grape cluster assignment
-> GrowthEngine recommendations -> memory bridge / expert proposal review
-> feedback -> benchmarks -> TrainingDataExporter -> optional future training review
```

The current implementation adds deterministic local-first foundations for dataset manifests, JSONL ingestion, donor proposals, knowledge seeds, validation, review, grape clustering, GrowthEngine recommendations, BenchmarkSuite measurement, and conservative training example export.

## Current Structures

Dataset manifest ingestion:

- `DatasetManifest`
- `DatasetLicensePolicy`
- `JsonlDatasetRecord`
- `DatasetIngestor`
- `DatasetIngestionReport`

Dataset ingestion:

- `DatasetSource`
- `DatasetSample`
- `InstructionDatasetSample`
- `ConversationDatasetSample`
- `AlpacaFormatAdapter`
- `ShareGPTFormatAdapter`

Donor proposals:

- `DonorModelProposal`
- `DonorModelAdapter`
- `StaticDonorModelAdapter`
- `LMStudioAdapter`
- `DonorProposalCollector`
- `DonorProposalBatch`
- `DonorProposalError`

Knowledge review:

- `KnowledgeSource`
- `KnowledgeSeed`
- `ValidationResult`
- `KnowledgeValidator`
- `NormalizedKnowledge`
- `KnowledgeDeduplicator`
- `KnowledgeConflictDetector`
- `KnowledgeReviewPipeline`
- `SeedReviewDecision`

Grape growth:

- `GrapeNode`
- `GrapeCluster`
- `GrapeAssignment`
- `GrapeClusterer`
- `GrowthDecision`
- `GrowthPlan`
- `GrowthEngineConfig`
- `GrowthEngine`

Measurement:

- `BenchmarkCase`
- `BenchmarkRunConfig`
- `BenchmarkResult`
- `BenchmarkReport`
- `BenchmarkSuite`

Training export:

- `TrainingExample`
- `TrainingDataset`
- `TrainingExportConfig`
- `TrainingDataExporter`

## Dataset Manifests In Growth Lab

`DatasetManifest` keeps dataset provenance explicit before any row can become a Growth Lab candidate. It records source, format, license, allowed uses, domains, capabilities, review requirements, and metadata.

`DatasetLicensePolicy` is conservative. It can allow knowledge seed candidates while still rejecting training export candidates when the license is unknown or restricted. This helps Grona avoid treating parsed dataset text as automatically trusted or training-safe.

`DatasetIngestor` parses tiny JSONL records, normalizes Alpaca-like, ShareGPT-like, and generic text rows, attaches manifest metadata, and returns a `DatasetIngestionReport`. It does not promote rows into durable memory or training data.

## Donor Model Proposals In Growth Lab

Donor adapters are proposal sources, not trusted knowledge engines. A donor adapter may suggest a route hint, summary, context hint, module suggestion, benchmark answer, or raw knowledge seed candidate. The output keeps its source, proposal type, confidence, and metadata so review layers can decide what to do with it.

The current foundation includes two adapters:

- `StaticDonorModelAdapter` for deterministic offline demos and tests
- `LMStudioAdapter` for explicitly configured local LM Studio experiments

`knowledge_seed_from_donor_proposal` can bridge a `knowledge_seed` proposal into a raw `KnowledgeSeed` candidate. That candidate still needs validation, review, deduplication, conflict checks, and benchmark impact checks before it can be treated as durable knowledge or training material.

## TrainingDataExporter In Growth Lab

`TrainingDataExporter` is a safe export boundary before any future specialized expert training experiments. It turns reviewed or validated internal records into explicit `TrainingExample` candidates and groups them into a deterministic `TrainingDataset`.

The exporter preserves:

- source and provenance metadata
- license metadata when available
- validation status
- domains and capabilities
- feedback, benchmark, review, or seed metadata

Default policy is conservative. Raw records, rejected seeds, and raw donor proposals are skipped. Synthetic demo benchmark traces are allowed because they are deterministic examples, not claims of real model quality. The exporter can produce Grona-native JSONL strings with metadata preserved and Alpaca-like JSONL strings with `instruction`, `input`, and `output` only.

This layer does not train models, write files by default, download datasets, call LM Studio, call LLMs, or claim exported records are ready for production training.

## BenchmarkSuite In Growth Lab

BenchmarkSuite gives Growth Lab a deterministic way to compare before/after states. It can run small demo tasks against baseline routing, demo memory, dataset-derived seeds, grape cluster memory, GrowthEngine decisions, and orchestration.

This helps answer local prototype questions:

- Did Grona select the expected modules?
- Did route-scoped context contain expected keywords?
- Did GrowthEngine produce relevant traces?
- Did dataset ingestion and grape clusters improve available context?
- Can dataset manifests preserve license and provenance before rows influence knowledge?
- Can donor-derived proposals be measured before they influence durable knowledge?
- Can training export candidates preserve validation and provenance before future use?
- Can a change be compared against baseline routing?

It does not judge natural-language answers or prove model quality.

## CLI Demos

```bash
python -m grona --growth-demo
python -m grona --growth-review-demo
python -m grona --grape-demo
python -m grona --growth-engine-demo
python -m grona --dataset-demo
python -m grona --jsonl-dataset-demo
python -m grona --benchmark-demo
python -m grona "Summarize modular routing" --donor-demo
python -m grona --training-export-demo
```

## Examples

```bash
python examples/knowledge_seed_demo.py
python examples/knowledge_review_demo.py
python examples/grape_cluster_demo.py
python examples/growth_engine_demo.py
python examples/dataset_ingestion_demo.py
python examples/jsonl_dataset_ingestion_demo.py
python examples/benchmark_demo.py
python examples/donor_model_demo.py
python examples/training_export_demo.py
```

## Current Limitations

- No autonomous self-training.
- No automatic expert creation.
- No model weights.
- No real dataset downloads.
- No Hugging Face integration or `datasets` dependency.
- No Parquet reader.
- No large dataset streaming.
- No large dataset files or generated dataset artifacts.
- No JSONL file writing by default.
- No web fact-checking.
- No temporal freshness checks.
- No semantic embeddings.
- No vector database.
- No LLM-based contradiction detection.
- No external judge model.
- No external evidence lookup.
- No automatic truth resolution.
- No default LM Studio execution.
- No default external donor model calls.
- No trusted donor model workflow.
- No raw donor proposal training export by default.
- No automatic promotion from dataset sample to trusted memory or expert behavior.
- No persisted dataset manifest, donor proposal, seed, cluster, growth plan, benchmark, or training dataset store.
- No semantic clustering.
- No production knowledge-quality, benchmark-accuracy, or training-data-quality claims.

The current Growth Lab layer is a deterministic heuristic prototype for future experiments.
