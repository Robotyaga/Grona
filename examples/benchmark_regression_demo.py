from grona import (
    BenchmarkRunConfig,
    BenchmarkSuite,
    InMemoryBenchmarkRunStore,
    compare_benchmark_runs,
    create_benchmark_run_record,
    create_demo_benchmark_cases,
)


def main() -> None:
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
        "example-baseline-001",
        created_at="2026-01-01T00:00:00+00:00",
    )
    candidate = create_benchmark_run_record(
        candidate_report,
        "example-candidate-001",
        created_at="2026-01-01T00:01:00+00:00",
    )
    store = InMemoryBenchmarkRunStore((baseline, candidate))
    regression = compare_benchmark_runs(baseline, candidate)

    print(f"Stored benchmark runs: {store.count()}")
    print(regression.to_text())
    print("\nStable JSON snapshot:")
    print(regression.to_json())


if __name__ == "__main__":
    main()
