from grona import (
    ExperimentGateConfig,
    ExperimentRegressionGate,
    ExperimentRunner,
    create_demo_benchmark_cases,
    create_demo_experiment_configs,
)


def main() -> None:
    runner = ExperimentRunner(
        create_demo_benchmark_cases(),
        create_demo_experiment_configs(),
        baseline_config_name="routing-only",
        regression_threshold=0.03,
    )
    _results, comparison = runner.run_and_compare()

    warning_config = ExperimentGateConfig(
        overall_regression_threshold=0.03,
        routing_regression_threshold=0.03,
        context_regression_threshold=0.03,
        growth_regression_threshold=0.03,
        case_regression_threshold=0.05,
        warning_only=True,
    )
    strict_config = ExperimentGateConfig(
        overall_regression_threshold=0.03,
        routing_regression_threshold=0.03,
        context_regression_threshold=0.03,
        growth_regression_threshold=0.03,
        case_regression_threshold=0.05,
        warning_only=False,
    )

    warning_decision = ExperimentRegressionGate(warning_config).evaluate(comparison)
    strict_decision = ExperimentRegressionGate(strict_config).evaluate(comparison)

    print("Warning-only gate:")
    print(warning_decision.to_text())
    print("\nStrict gate:")
    print(strict_decision.to_text())
    print("\nStable warning decision JSON:")
    print(warning_decision.to_json())


if __name__ == "__main__":
    main()
