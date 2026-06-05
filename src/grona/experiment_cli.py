"""CLI demo for deterministic experiment comparisons."""

from __future__ import annotations

from collections.abc import Sequence

from .benchmarks import create_demo_benchmark_cases
from .experiments import ExperimentRunner, create_demo_experiment_configs


def format_experiment_demo() -> str:
    """Run deterministic experiment comparison demo and format the report."""
    runner = ExperimentRunner(
        create_demo_benchmark_cases(),
        create_demo_experiment_configs(),
        baseline_config_name="routing-only",
        regression_threshold=0.03,
    )
    results, comparison = runner.run_and_compare()
    lines = [
        "ExperimentRunner Grona-vs-monolith demo",
        "Execution: deterministic local scoring only; no LLMs, APIs, downloads, or training.",
        "",
        f"Configs run: {len(results)}",
        comparison.to_text(),
        "",
        "JSON preview:",
        comparison.to_json(),
    ]
    return "\n".join(lines).rstrip()


def main(argv: Sequence[str] | None = None) -> int:
    """Run the experiment comparison demo helper."""
    _ = argv
    print(format_experiment_demo())
    return 0
