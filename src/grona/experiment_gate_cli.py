"""CLI demo for deterministic experiment regression gates."""

from __future__ import annotations

from collections.abc import Sequence

from .benchmarks import create_demo_benchmark_cases
from .experiments import (
    ExperimentGateConfig,
    ExperimentRegressionGate,
    ExperimentRunner,
    create_demo_experiment_configs,
)


def create_demo_comparison():
    """Run deterministic experiment configs and return their comparison report."""
    runner = ExperimentRunner(
        create_demo_benchmark_cases(),
        create_demo_experiment_configs(),
        baseline_config_name="routing-only",
        regression_threshold=0.03,
    )
    _results, comparison = runner.run_and_compare()
    return comparison


def format_experiment_gate_demo(strict: bool = False) -> str:
    """Run deterministic experiment gate demo and format the threshold report."""
    comparison = create_demo_comparison()
    config = ExperimentGateConfig(
        overall_regression_threshold=0.03,
        routing_regression_threshold=0.03,
        context_regression_threshold=0.03,
        growth_regression_threshold=0.03,
        case_regression_threshold=0.05,
        warning_only=not strict,
        metadata={"demo": "experiment-gate", "strict": strict},
    )
    decision = ExperimentRegressionGate(config).evaluate(comparison)
    lines = [
        "ExperimentRegressionGate demo",
        "Execution: deterministic local thresholds only; no LLMs, APIs, downloads, or training.",
        f"Mode: {'strict' if strict else 'warning-only'}",
        "",
        comparison.to_text(),
        "",
        decision.to_text(),
        "",
        "Gate config JSON:",
        config.to_json(),
        "",
        "Gate decision JSON:",
        decision.to_json(),
    ]
    return "\n".join(lines).rstrip()


def main(argv: Sequence[str] | None = None) -> int:
    """Run the experiment regression gate demo helper."""
    args = tuple(argv or ())
    strict = "--experiment-gate-strict-demo" in args
    print(format_experiment_gate_demo(strict=strict))
    return 0
