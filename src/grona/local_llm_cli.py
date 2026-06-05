"""CLI demo for explicit local LLM baseline adapters."""

from __future__ import annotations

from collections.abc import Sequence

from .benchmarks import create_demo_benchmark_cases
from .experiments import ExperimentConfig, ExperimentRunner
from .local_llm import LocalLLMBaselineRunner, StaticLocalLLMAdapter

DEMO_TASK = "Explain sparse routing for a local-first modular AI prototype."


def format_local_llm_static_demo() -> str:
    """Run deterministic static local LLM baseline demo and format output."""
    adapter = StaticLocalLLMAdapter(mode="weak_monolith")
    baseline = LocalLLMBaselineRunner(adapter).run(DEMO_TASK)
    configs = (
        ExperimentConfig("routing-only", "Routing baseline.", "routing_only"),
        ExperimentConfig(
            "local-llm-static",
            "Static local LLM baseline adapter without network calls.",
            "local_llm_baseline",
        ),
    )
    runner = ExperimentRunner(
        create_demo_benchmark_cases(),
        configs,
        baseline_config_name="routing-only",
        local_llm_adapter=adapter,
    )
    _results, comparison = runner.run_and_compare()
    lines = [
        "Local LLM baseline static demo",
        "Execution: deterministic static adapter only; no LM Studio, APIs, downloads, or training.",
        "",
        baseline.to_text(),
        "",
        comparison.to_text(),
        "",
        "Baseline result JSON:",
        baseline.to_json(),
    ]
    return "\n".join(lines).rstrip()


def main(argv: Sequence[str] | None = None) -> int:
    """Run the local LLM static baseline demo helper."""
    _ = argv
    print(format_local_llm_static_demo())
    return 0
