# Benchmarking

BenchmarkSuite is Grona's deterministic benchmark layer for early research comparisons.

It answers a narrow prototype question: did a Grona configuration select the expected modules, build relevant local context, and expose useful GrowthEngine signals for small demo tasks?

It does not judge model answers. It does not call an LLM, use an external judge, download datasets, create embeddings, train models, or claim real accuracy.

## Current Flow

```text
BenchmarkCase -> BenchmarkRunConfig -> BenchmarkSuite -> BenchmarkReport
BenchmarkReport -> BenchmarkRunRecord -> BenchmarkRunStore -> BenchmarkRegressionReport
ExperimentConfig -> ExperimentRunner -> ExperimentResult -> ExperimentComparisonReport
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

`BenchmarkRunRecord` wraps one report with run id, creation time, optional git commit, metadata, and a schema version. `InMemoryBenchmarkRunStore` is for tests and demos. `JsonlBenchmarkRunStore` writes explicit JSONL snapshots only when a caller provides a path.

`BenchmarkRegressionReport` compares two saved run records and reports average score deltas plus per-case improved, regressed, and unchanged groups.

`ExperimentRunner` runs multiple deterministic configurations side by side and produces one comparison report.

## ExperimentRunner

`ExperimentConfig` describes one deterministic experiment config with:

- `name`
- `description`
- `mode`
- `metadata`

Current modes are:

- `routing_only`
- `orchestrated_context`
- `memory_context`
- `growth_trace`
- `monolith_stub`

`ExperimentRunner` accepts benchmark cases and experiment configs. It reuses `BenchmarkSuite` for Grona configs, wraps each report in a `BenchmarkRunRecord`, and uses regression comparison helpers to compute deltas against the baseline config.

`ExperimentComparisonReport` includes:

- baseline config name
- candidate config names
- per-config score summaries
- score deltas vs baseline
- best config by overall score
- improved and regressed configs
- per-case best config and scores
- deterministic human-readable summary

Run the demo:

```bash
python -m grona --experiment-demo
python examples/experiment_comparison_demo.py
```

The demo runs routing-only, memory-context, growth-trace, and monolith-stub configs. It does not call models, network, LM Studio, APIs, downloads, embeddings, or training.

## Monolith Stub

`MonolithBaseline` is a deterministic broad baseline stub. It simulates a generic system with weak broad coverage, no explicit module selection trace, no real context routing, and no GrowthEngine trace.

It is not a real monolithic LLM. It does not prove that Grona is better than a monolithic model. It only prepares the shape of future Grona-vs-monolith experiments.

## What It Can Measure Now

Benchmark and experiment layers can score:

- whether expected module names were selected
- whether expected high-level domains were selected
- whether expected keywords appeared in task context, memory, grape clusters, or growth traces
- whether GrowthEngine produced relevant deterministic signals
- whether enhanced local configurations improve the available context score compared with baseline routing
- whether a candidate benchmark snapshot regressed against a saved baseline by a deterministic threshold
- which deterministic experiment config has the best average overall score under the current rubric

Scores are deterministic floats from `0.0` to `1.0`.

## Run Persistence And Regression Snapshots

Benchmark run persistence is intentionally small and inspectable:

- `benchmark_report_to_dict()` and `benchmark_report_from_dict()` serialize benchmark reports without changing scoring logic.
- `BenchmarkRunRecord` stores one immutable benchmark snapshot wrapper.
- `InMemoryBenchmarkRunStore` keeps deterministic records for tests and demos.
- `JsonlBenchmarkRunStore` appends explicit local JSONL records when a caller asks for file persistence.
- `compare_benchmark_runs()` compares two records and returns a `BenchmarkRegressionReport`.

Regression comparison is score-based only. Missing candidate cases are marked as regressions, new candidate cases are marked as improvements, and small deltas inside the threshold are unchanged.

Run the snapshot demo:

```bash
python -m grona --benchmark-regression-demo
python examples/benchmark_regression_demo.py
```

## What It Cannot Measure Yet

BenchmarkSuite and ExperimentRunner cannot measure real model intelligence or real answer quality yet.

Current limitations:

- no LLM output evaluation
- no real monolithic LLM baseline
- no LM Studio adapter use in benchmark or experiment demos
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
- no statistical significance claims for regression snapshots or experiment comparisons

## Why Deterministic Scoring First

Grona is still building its architecture contracts. Deterministic scoring keeps early regressions visible before model uncertainty enters the system.

This makes it easier to see whether a code change broke routing, context assembly, dataset seed conversion, grape clustering, growth decisions, benchmark snapshot serialization, or experiment comparison output.

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

`create_demo_experiment_configs()` includes:

- `routing-only`
- `memory-context`
- `growth-trace`
- `monolith-stub`

## Running

```bash
python -m grona --benchmark-demo
python -m grona --benchmark-regression-demo
python -m grona --experiment-demo
python examples/benchmark_demo.py
python examples/benchmark_regression_demo.py
python examples/experiment_comparison_demo.py
pytest
```

The CLI prints compact reports with average routing, context, growth, and overall scores. The experiment demo prints per-config summaries, deltas against the routing-only baseline, the best config, and a stable JSON preview.

## Preparing Grona-vs-Monolith Experiments

The current layer is not a Grona-vs-monolith result. It is the measuring harness that can later compare:

- baseline routing
- Grona with memory
- Grona with ingested dataset seeds
- Grona with grape clusters
- Grona with GrowthEngine decisions
- deterministic monolith stub
- future monolithic model adapters
- future local LLM adapters

Future work can add human review, optional LLM judges, task output rubrics, persisted baseline selection, CI regression gates, local LLM baselines, and adapter comparisons without changing the principle that benchmark traces must stay explicit and reviewable.
