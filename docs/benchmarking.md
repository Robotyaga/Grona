# Benchmarking

BenchmarkSuite is Grona's deterministic benchmark layer for early research comparisons.

It answers a narrow prototype question: did a Grona configuration select the expected modules, build relevant local context, and expose useful GrowthEngine signals for small demo tasks?

It does not judge model answers. It does not call an LLM, use an external judge, download datasets, create embeddings, train models, or claim real accuracy.

## Current Flow

```text
BenchmarkCase -> BenchmarkRunConfig -> BenchmarkSuite -> BenchmarkReport
```

A `BenchmarkCase` defines a task with expected domains, modules, and keywords.

A `BenchmarkRunConfig` turns deterministic components on or off:

- baseline routing
- demo memory
- dataset seed normalization
- grape cluster memory
- GrowthEngine recommendations
- orchestration

`BenchmarkSuite` runs every case with a config and returns a `BenchmarkReport` with per-case `BenchmarkResult` values.

## What It Can Measure Now

BenchmarkSuite can score:

- whether expected module names were selected
- whether expected high-level domains were selected
- whether expected keywords appeared in task context, memory, grape clusters, or growth traces
- whether GrowthEngine produced relevant deterministic signals
- whether enhanced local configurations improve the available context score compared with baseline routing

Scores are deterministic floats from `0.0` to `1.0`.

## What It Cannot Measure Yet

BenchmarkSuite cannot measure real model intelligence or real answer quality yet.

Current limitations:

- no LLM output evaluation
- no LM Studio adapter
- no OpenAI API
- no external judge model
- no human evaluation workflow
- no large benchmark datasets
- no dataset downloads
- no embeddings or semantic matching
- no vector database
- no training or fine-tuning
- no production orchestration claims
- no automatic accuracy claims

## Why Deterministic Scoring First

Grona is still building its architecture contracts. Deterministic scoring keeps early regressions visible before model uncertainty enters the system.

This makes it easier to see whether a code change broke routing, context assembly, dataset seed conversion, grape clustering, or growth decisions.

The scoring helpers are intentionally simple:

- `domain_match_score()` checks expected domain coverage.
- `module_match_score()` checks expected module coverage.
- `keyword_context_score()` checks expected keyword coverage in local context text.
- `growth_decision_score()` checks whether growth traces overlap expected domains and keywords.
- `overall_benchmark_score()` combines routing, context, and growth scores.

## Demo Cases

`create_demo_benchmark_cases()` includes small deterministic cases for:

- automotive cooling and overheating
- cybersecurity/code review
- media/video workflow
- document retrieval
- general instruction following

`create_demo_benchmark_configs()` includes:

- `baseline-routing`
- `orchestrated-demo-memory`
- `dataset-growth-demo`

## Running

```bash
python -m grona --benchmark-demo
python examples/benchmark_demo.py
pytest
```

The CLI prints compact reports with average routing, context, growth, and overall scores. It also shows a simple baseline-versus-enhanced comparison.

## Preparing Grona-vs-Monolith Experiments

The current layer is not a Grona-vs-monolith result. It is the measuring harness that can later compare:

- baseline routing
- Grona with memory
- Grona with ingested dataset seeds
- Grona with grape clusters
- Grona with GrowthEngine decisions
- future monolithic model adapters
- future local LLM adapters

Future work can add human review, optional LLM judges, task output rubrics, and adapter comparisons without changing the principle that benchmark traces must stay explicit and reviewable.
