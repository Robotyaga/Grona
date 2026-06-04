# Grona

[![tests](https://github.com/Robotyaga/Grona/actions/workflows/tests.yml/badge.svg)](https://github.com/Robotyaga/Grona/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Grona is a lightweight research prototype for explainable sparse AI routing. Instead of activating every capability for every task, it routes work through a small cluster of relevant expert modules and keeps the route trace visible.

The metaphor is a grape cluster. A workspace is the vineyard, expert modules are active grapes, dataset samples and memory sources are nutrients, routing rules decide which grapes wake up, GrowthEngine recommends future growth actions, BenchmarkSuite measures deterministic traces, and safety policy is the protective layer around future tool use.

## Current Status

Grona is deterministic and local-first. It does not call an LLM, execute shell commands, use external APIs, crawl files, parse PDFs, build embeddings, train models, download datasets, or run real tools.

What it does today:

- routes tasks through an explainable `Router`
- stores modules in a `ModuleRegistry`
- adjusts routing with optional feedback-informed scoring
- builds route-scoped context from deterministic memory modules
- ingests in-memory demo documents into memory records
- normalizes tiny Alpaca-like and ShareGPT-like in-memory dataset samples
- converts normalized dataset samples into raw `KnowledgeSeed` values with license metadata
- validates and reviews raw `KnowledgeSeed` values before future promotion
- groups promote-candidate seeds into deterministic `GrapeCluster` and `GrapeNode` structures
- produces deterministic `GrowthDecision` and `GrowthPlan` recommendations
- runs deterministic benchmark cases with `BenchmarkSuite`
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

Run deterministic Growth Lab and benchmark demos:

```bash
python -m grona --growth-demo
python -m grona --growth-review-demo
python -m grona --grape-demo
python -m grona --growth-engine-demo
python -m grona --dataset-demo
python -m grona --benchmark-demo
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
python examples/benchmark_demo.py
```

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
- Routing, memory retrieval, clustering, growth, and benchmarking are deterministic heuristics.
- BenchmarkSuite is a deterministic rubric only; it does not evaluate real LLM answers.
- Dataset ingestion is in-memory normalization only; it does not download or read real datasets.
- No Hugging Face integration, `datasets` dependency, JSONL loader, or Parquet reader yet.
- No real LLM integration, donor model adapter, LM Studio adapter, or external judge model yet.
- No embeddings, semantic clustering, vector database, SQL database, or web server.
- No autonomous self-training, model weights, training-data export, or automatic expert creation yet.
- No real tool execution, shell execution, subprocesses, filesystem tools, or network tools.
- No real sandboxing or process isolation.
- Safety policy is planning/policy evaluation only, not a security boundary.

These limits are intentional. Grona is a public research/prototype foundation for sparse modular AI architecture, not a production claim.
