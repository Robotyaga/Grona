from grona import ExperimentRunner, create_demo_benchmark_cases, create_demo_experiment_configs


def main() -> None:
    runner = ExperimentRunner(
        create_demo_benchmark_cases(),
        create_demo_experiment_configs(),
        baseline_config_name="routing-only",
    )
    results, comparison = runner.run_and_compare()

    print(f"Experiment results: {len(results)}")
    print(comparison.to_text())
    print("\nStable JSON snapshot:")
    print(comparison.to_json())


if __name__ == "__main__":
    main()
