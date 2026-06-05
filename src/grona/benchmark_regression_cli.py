"""CLI demo for benchmark run persistence and regression snapshots."""

from __future__ import annotations

from collections.abc import Sequence

from .benchmark_runs import (
    InMemoryBenchmarkRunStore,
    compare_benchmark_runs,
    create_benchmark_run_record,
)
from .benchmarks import BenchmarkRunConfig, BenchmarkSuite, create_demo_benchmark_cases


def format_benchmark_regression_demo() -> str:
    """Run a deterministic benchmark regression snapshot demo."""
    suite = BenchmarkSuite(create_demo_benchmark_cases())
    baseline_report = suite.run(BenchmarkRunConfig("baseline-routing"))
    candidate_report = suite.run(
        BenchmarkRunConfig(
            "candidate-demo-memory",
            use_memory=True,
            use_demo_memory=True,
            use_orchestrator=True,
        )
    )
    baseline = create_benchmark_run_record(
        baseline_report,
        run_id="demo-baseline-001",
        created_at="2026-01-01T00:00:00+00:00",
        metadata={"demo": True, "role": "baseline"},
    )
    candidate = create_benchmark_run_record(
        candidate_report,
        run_id="demo-candidate-001",
        created_at="2026-01-01T00:01:00+00:00",
        metadata={"demo": True, "role": "candidate"},
    )
    store = InMemoryBenchmarkRunStore((baseline, candidate))
    regression = compare_benchmark_runs(baseline, candidate, regression_threshold=0.03)

    lines = [
        "Benchmark regression snapshot demo",
        "Execution: deterministic local scoring only; no LLMs, APIs, downloads, or training.",
        "",
        f"Stored runs: {store.count()}",
        f"Baseline: {baseline.run_id} ({baseline.config_name})",
        f"Candidate: {candidate.run_id} ({candidate.config_name})",
        "",
        regression.to_text(),
        "",
        "JSON preview:",
        regression.to_json(),
    ]
    return "\n".join(lines).rstrip()


def main(argv: Sequence[str] | None = None) -> int:
    """Run the benchmark regression snapshot demo helper."""
    _ = argv
    print(format_benchmark_regression_demo())
    return 0
