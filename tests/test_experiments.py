from grona import (
    BenchmarkCase,
    ExperimentConfig,
    ExperimentResult,
    ExperimentRunner,
    MonolithBaseline,
    best_experiment_result,
    create_benchmark_run_record,
    create_demo_benchmark_cases,
    create_demo_experiment_configs,
)
from grona.entrypoint import main as entrypoint_main
from grona.experiment_cli import format_experiment_demo


def test_experiment_config_creation() -> None:
    config = ExperimentConfig(
        "routing-only",
        "Baseline routing only.",
        "routing_only",
        metadata={"suite": "demo"},
    )

    assert config.name == "routing-only"
    assert config.description == "Baseline routing only."
    assert config.mode == "routing_only"
    assert config.metadata["suite"] == "demo"
    assert config.to_benchmark_run_config().name == "routing-only"


def test_experiment_config_rejects_unknown_mode() -> None:
    try:
        ExperimentConfig("bad", "Unsupported mode.", "not-real")
    except ValueError as exc:
        assert "unsupported experiment mode" in str(exc)
    else:
        raise AssertionError("expected unsupported mode to fail")


def test_monolith_stub_is_deterministic() -> None:
    cases = create_demo_benchmark_cases()
    first = MonolithBaseline("monolith-stub").run(cases)
    second = MonolithBaseline("monolith-stub").run(cases)

    assert first == second
    assert first.config_name == "monolith-stub"
    assert all(result.selected_modules == ("monolith-stub",) for result in first.results)
    assert first.average_growth_score == 0.0


def test_experiment_result_exposes_scores() -> None:
    report = MonolithBaseline("monolith-stub").run(create_demo_benchmark_cases())
    run = create_benchmark_run_record(report, "run-1")
    config = ExperimentConfig("monolith-stub", "Deterministic stub.", "monolith_stub")
    result = ExperimentResult(config, run, "summary")

    assert result.overall_score == report.average_overall_score
    assert result.routing_score == report.average_routing_score
    assert result.context_score == report.average_context_score
    assert result.growth_score == report.average_growth_score
    assert result.case_count == len(report.results)
    assert result.to_dict()["mode"] == "monolith_stub"


def test_experiment_runner_runs_multiple_configs() -> None:
    runner = ExperimentRunner(
        create_demo_benchmark_cases(),
        create_demo_experiment_configs(),
        baseline_config_name="routing-only",
    )

    results = runner.run()

    assert len(results) == 4
    assert [result.config.name for result in results] == [
        "routing-only",
        "memory-context",
        "growth-trace",
        "monolith-stub",
    ]
    assert all(result.case_count == len(create_demo_benchmark_cases()) for result in results)


def test_experiment_comparison_selects_best_config_deterministically() -> None:
    runner = ExperimentRunner(
        create_demo_benchmark_cases(),
        create_demo_experiment_configs(),
        baseline_config_name="routing-only",
    )

    results, comparison = runner.run_and_compare()

    assert comparison.baseline_config_name == "routing-only"
    assert comparison.best_config_name == best_experiment_result(results).config.name
    assert comparison.candidate_config_names == (
        "growth-trace",
        "memory-context",
        "monolith-stub",
    )
    assert comparison.to_json() == comparison.to_json()


def test_experiment_comparison_deltas_vs_baseline_are_correct() -> None:
    runner = ExperimentRunner(
        create_demo_benchmark_cases(),
        create_demo_experiment_configs(),
        baseline_config_name="routing-only",
    )

    results, comparison = runner.run_and_compare()
    by_name = {result.config.name: result for result in results}
    expected = round(
        by_name["growth-trace"].overall_score - by_name["routing-only"].overall_score,
        3,
    )

    assert comparison.deltas_vs_baseline["growth-trace"]["overall"] == expected
    assert "growth-trace" in comparison.improved_configs
    assert "monolith-stub" in comparison.regressed_configs


def test_experiment_runner_accepts_custom_cases() -> None:
    cases = (
        BenchmarkCase(
            "general-case",
            "Analyze a plan and explain steps.",
            expected_domains=("general",),
            expected_modules=("general-reasoning",),
            expected_keywords=("analyze", "plan", "explain", "steps"),
        ),
    )
    configs = (
        ExperimentConfig("routing-only", "Routing baseline.", "routing_only"),
        ExperimentConfig("monolith-stub", "Monolith stub.", "monolith_stub"),
    )

    results, comparison = ExperimentRunner(cases, configs).run_and_compare()

    assert len(results) == 2
    assert comparison.per_case_comparison["general-case"]["best_config"] in {
        "routing-only",
        "monolith-stub",
    }


def test_experiment_cli_demo_behavior() -> None:
    output = format_experiment_demo()

    assert "ExperimentRunner Grona-vs-monolith demo" in output
    assert "Configs run: 4" in output
    assert "Experiment comparison report" in output
    assert "Best config:" in output
    assert "JSON preview:" in output


def test_entrypoint_routes_experiment_demo(capsys) -> None:
    status = entrypoint_main(("--experiment-demo",))
    output = capsys.readouterr().out

    assert status == 0
    assert "ExperimentRunner Grona-vs-monolith demo" in output
