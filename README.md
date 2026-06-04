# Grona

[![tests](https://github.com/Robotyaga/Grona/actions/workflows/tests.yml/badge.svg)](https://github.com/Robotyaga/Grona/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Grona is a lightweight research prototype for explainable sparse AI routing. Instead of activating every capability for every task, it routes work through a small cluster of relevant expert modules and keeps the route trace visible.

The metaphor is a grape cluster. A workspace is the vineyard, expert modules are active grapes, dataset manifests, dataset samples, deterministic dataset reviews, donor proposals, feedback traces, benchmark traces, and memory sources are nutrients, routing rules decide which grapes wake up, GrowthEngine recommends future growth actions, BenchmarkSuite measures deterministic traces, TrainingDataExporter prepares reviewed records for future experiments, and safety policy is the protective layer around future tool use.

## Current Status

Grona is deterministic and local-first. It does not call an LLM by default, execute shell commands, use external APIs, crawl files, parse PDFs, build embeddings, train models, download datasets, or run real tools.

What it does today:

- routes tasks through an explainable `Router`
- stores modules in a `ModuleRegistry`
- adjusts routing with optional feedback-informed scoring
- builds route-scoped context from deterministic memory modules
- ingests in-memory demo documents into memory records
- describes small dataset sources with `DatasetManifest`
- parses tiny explicit JSONL text or files into line-aware records
- applies conservative `DatasetLicensePolicy` checks before dataset use
- normalizes tiny Alpaca-like, ShareGPT-like, and generic text dataset samples
- reviews normalized dataset samples with deterministic quality checks before seed use
- converts only accepted reviewed dataset samples into raw `KnowledgeSeed` candidates
- collects deterministic donor model proposals through a static offline adapter
- defines an optional LM Studio adapter foundation behind explicit user configuration
- converts donor `knowledge_seed` proposals into raw untrusted `KnowledgeSeed` candidates
- validates and reviews raw `KnowledgeSeed` values before future promotion
- groups promote-candidate seeds into deterministic `GrapeCluster` and `GrapeNode` structures
- produces deterministic `GrowthDecision` and `GrowthPlan` recommendations
- runs deterministic benchmark cases with `BenchmarkSuite`
- exports conservative in-memory training example candidates with `TrainingDataExporter`
- orchestrates selected modules into structured handoffs
- runs deterministic demo expert executors, execution adapters, and mock tools
- supports built-in workspace profiles
- ships examples, tests, CI, and documentation

## Quickstart

```bash
pip install -e .
python -m grona "Review firewall logs for suspicious port scans"
```

For tests and linting:

```bash
pip install -e .[dev]
pytest
ruff check .
```

## CLI Examples

```bash
python -m grona "Diagnose engine overheating" --workspace automotive
python -m grona "Review this Python script for security issues" --workspace cybersecurity
python -m grona "Plan MotionCam RAW workflow" --workspace media
python -m grona "Find document indexing notes" --workspace documents
```

Run deterministic Growth Lab, dataset, benchmark, donor, and training export demos:

```bash
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
```

Build context and run deterministic adapters or mock tools:

```bash
python -m grona "Diagnose engine overheating" --orchestrate --use-demo-memory
python -m grona "Diagnose engine overheating" --orchestrate --ingest-demo-docs
python -m grona "Review this project" --use-demo-adapters --dry-run-tools
python -m grona "Analyze engine overheating symptoms" --use-demo-tools
```

## Demo Scripts

```bash
python examples/basic_routing_demo.py
python examples/feedback_demo.py
python examples/adaptive_routing_demo.py
python examples/orchestration_demo.py
python examples/memory_demo.py
python examples/expert_execution_demo.py
python examples/execution_adapters_demo.py
python examples/safety_policy_demo.py
python examples/tool_adapter_demo.py
python examples/document_ingestion_demo.py
python examples/workspace_profile_demo.py
python examples/knowledge_seed_demo.py
python examples/knowledge_review_demo.py
python examples/grape_cluster_demo.py
python examples/growth_engine_demo.py
python examples/dataset_ingestion_demo.py
python examples/jsonl_dataset_ingestion_demo.py
python examples/dataset_review_demo.py
python examples/donor_model_demo.py
python examples/benchmark_demo.py
python examples/training_export_demo.py
```

## Dataset Manifest, JSONL, And Quality Review

`DatasetManifest` records where a dataset source came from, what format it uses, which license applies, which uses are allowed, which domains and capabilities are relevant, and whether review is required. `DatasetLicensePolicy` keeps use decisions explicit and conservative.

`DatasetIngestor` can parse tiny JSONL records, normalize Alpaca-like, ShareGPT-like, and generic text rows, attach manifest provenance, and return a `DatasetIngestionReport`. This prepares dataset rows as candidates only; it does not download datasets, trust rows, train models, or promote anything into durable knowledge.

`DatasetQualityReviewer` is the next deterministic gate. It reviews normalized samples for empty or too-short content, duplicate normalized text, missing output or assistant answers, suspicious prompt markers, unsupported sample types, license restrictions, optional domain mismatch, and low information density. It returns `DatasetSampleReview` decisions plus a `DatasetReviewReport`.

Accepted reviewed samples can become raw `KnowledgeSeed` candidates with review metadata preserved. Rejected or human-review samples are not promoted automatically. This is not an LLM judge, semantic deduplicator, legal review, or training-data quality guarantee.

## Donor Model Adapter Foundation

A donor model is a proposal source, not Grona's brain and not a trusted authority. The deterministic `StaticDonorModelAdapter` is used for tests and demos. `LMStudioAdapter` is an optional local-model adapter foundation that uses the Python standard library and only runs when explicitly configured by a caller.

Donor proposals can suggest summaries, route hints, context hints, benchmark answers, module suggestions, or raw `knowledge_seed` candidates. Donor `knowledge_seed` proposals can be converted into `KnowledgeSeed` values, but they still require validation, review, benchmarking, and human judgment before durable use.

## TrainingDataExporter Foundation

`TrainingDataExporter` prepares explicit in-memory training example candidates for future specialized expert training experiments. It preserves instruction, input, output, source, domains, capabilities, provenance, license, validation status, and metadata.

The default export policy is conservative:

- raw records are skipped
- rejected records are skipped
- synthetic demo benchmark examples are allowed
- metadata is preserved
- validation or review is required before export
- raw donor proposals are not exported by default

The exporter can produce deterministic Grona-native JSONL strings with metadata preserved and Alpaca-like JSONL strings containing `instruction`, `input`, and `output`. It does not write files by default and does not train a model.

## BenchmarkSuite MVP

BenchmarkSuite is a deterministic rubric and reporting layer. It can compare small local configurations such as baseline routing, orchestrated demo memory, and dataset-plus-growth demos.

It currently scores:

- expected domain coverage
- expected module coverage
- expected keyword coverage in built context and growth traces
- simple GrowthEngine relevance signals
- average routing, context, growth, and overall scores

This is not a model judge and does not claim real answer accuracy. See [Benchmarking](docs/benchmarking.md).

## Documentation

- [Architecture](docs/architecture.md)
- [Growth Lab](docs/growth-lab.md)
- [Dataset ingestion](docs/dataset-ingestion.md)
- [Benchmarking](docs/benchmarking.md)
- [Development notes](docs/development.md)
- [Workspace profiles](docs/workspaces.md)
- [Research notes](docs/research-notes.md)
- [Project vision](docs/project-vision.md)
- [Roadmap](docs/roadmap.md)
- [v0.1.0 prototype release notes](docs/release-notes-v0.1.0-prototype.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Changelog](CHANGELOG.md)

## Current Limitations

- This is a prototype, not a production assistant.
- Routing, memory retrieval, dataset ingestion, dataset review, clustering, growth, donor proposals, benchmarking, and training export are deterministic or explicitly configured prototype layers.
- Dataset rows are candidates only; they are not automatically trusted, promoted, or training-safe.
- Dataset quality review is deterministic only; it is not semantic deduplication, LLM judging, legal review, or a guarantee of real training quality.
- No dataset downloads, Hugging Face integration, `datasets` dependency, Parquet support, or large dataset streaming yet.
- Donor model output is untrusted proposal material, not validated truth.
- Raw donor proposals are not exported as training data by default.
- LM Studio support is optional and not used by default or by CI.
- BenchmarkSuite is a deterministic rubric only; it does not evaluate real LLM answers.
- TrainingDataExporter produces candidate records only; it does not train models or prove example quality.
- No real LLM integration, trusted donor model workflow, external judge model, or automatic answer generation yet.
- No embeddings, semantic clustering, vector database, SQL database, or web server.
- No autonomous self-training, model weights, or automatic expert creation yet.
- No real tool execution, shell execution, subprocesses, filesystem tools, or network tools.
- No real sandboxing or process isolation.
- Safety policy is planning/policy evaluation only, not a security boundary.

These limits are intentional. Grona is a public research/prototype foundation for sparse modular AI architecture, not a production claim.
