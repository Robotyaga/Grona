"""CLI helpers for deterministic BenchmarkSuite demos."""

from __future__ import annotations

from collections.abc import Sequence

from .benchmarks import BenchmarkReport, BenchmarkSuite, create_demo_benchmark_cases, create_demo_benchmark_configs


def format_benchmark_demo() -> str:
    """Run the deterministic benchmark demo and format compact reports."""
    cases = create_demo_benchmark_cases()
    configs = create_demo_benchmark_configs()
    suite = BenchmarkSuite(cases)
    reports = tuple(suite.run(config) for config in configs)
    lines = [
        "BenchmarkSuite MVP demo",
        (
            "Execution: deterministic local scoring only; no LLMs, APIs, embeddings, "
            "downloads, or training."
        ),
        "",
    ]
    for report in reports:
        lines.append(compact_report_text(report))
        lines.append("")
    baseline = reports[0]
    enhanced = reports[-1]
    delta = enhanced.average_overall_score - baseline.average_overall_score
    lines.extend(
        (
            "Comparison:",
            f"- baseline overall: {baseline.average_overall_score:.2f}",
            f"- enhanced overall: {enhanced.average_overall_score:.2f}",
            f"- delta: {delta:+.2f}",
        )
    )
    return "\n".join(lines).rstrip()


def compact_report_text(report: BenchmarkReport) -> str:
    """Format one report with averages and per-case summaries."""
    lines = [
        f"Report: {report.config_name}",
        (
            "Averages: "
            f"routing={report.average_routing_score:.2f}, "
            f"context={report.average_context_score:.2f}, "
            f"growth={report.average_growth_score:.2f}, "
            f"overall={report.average_overall_score:.2f}"
        ),
        "Cases:",
    ]
    for result in report.results:
        modules = ", ".join(result.selected_modules) or "none"
        lines.append(
            f"- {result.case_id}: overall={result.overall_score:.2f}; "
            f"modules={modules}; {result.summary}"
        )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the benchmark demo helper."""
    _ = argv
    print(format_benchmark_demo())
    return 0
