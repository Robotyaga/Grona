"""Run deterministic BenchmarkSuite comparisons for Grona."""

from grona import BenchmarkSuite, create_demo_benchmark_cases, create_demo_benchmark_configs


def main() -> None:
    """Compare baseline routing with enhanced deterministic Grona configs."""
    cases = create_demo_benchmark_cases()
    configs = create_demo_benchmark_configs()
    suite = BenchmarkSuite(cases)
    reports = [suite.run(config) for config in configs]

    print("BenchmarkSuite MVP example")
    print("Execution: deterministic local scoring only; no model calls or downloads.")
    print()
    for report in reports:
        print(report.to_text())
        print()

    baseline = reports[0]
    enhanced = reports[-1]
    print("Before/after comparison")
    print(f"Baseline overall: {baseline.average_overall_score:.2f}")
    print(f"Enhanced overall: {enhanced.average_overall_score:.2f}")
    print(f"Delta: {enhanced.average_overall_score - baseline.average_overall_score:+.2f}")
    print()
    print("This is a rubric trace, not an automatic model-quality claim.")


if __name__ == "__main__":
    main()
