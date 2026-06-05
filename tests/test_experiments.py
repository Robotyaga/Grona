from grona import (
    BenchmarkCase,
    ExperimentComparisonReport,
    ExperimentConfig,
    ExperimentGateConfig,
    ExperimentGateDecision,
    ExperimentRegressionGate,
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
from grona.experiment_gate_cli import format_experiment_gate_demo


def create_demo_comparison() -> ExperimentComparisonReport:
    runner = ExperimentRunner(
        create_demo_benchmark_cases(),
        create_demo_experiment_configs(),
        baseline_config_name="routing-only",
        regression_threshold=0.03,
    )
    _results, comparison = runner.run_and_compare()
    return comparison


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


def test_experiment_gate_config_defaults_are_warning_only() -> None:
    config = ExperimentGateConfig()

    assert config.warning_only is True
    assert config.fail_on_missing_scores is True
    assert config.overall_regression_threshold == 0.05
    assert config.case_regression_threshold == 0.10
    assert config.threshold_for_metric("overall") == 0.05
    assert config.to_json() == config.to_json()


def test_experiment_gate_config_rejects_negative_threshold() -> None:
    try:
        ExperimentGateConfig(overall_regression_threshold=-0.01)
    except ValueError as exc:
        assert "overall_regression_threshold cannot be negative" in str(exc)
    else:
        raise AssertionError("expected negative threshold to fail")


def test_experiment_gate_decision_serializes_deterministically() -> None:
    decision = ExperimentGateDecision(
        passed=True,
        warning_only=True,
        status="warning",
        reasons=("demo reason",),
        warning_metrics=("candidate:overall",),
        regressed_cases=("case-1:candidate",),
        summary="demo summary",
        metadata={"source": "test"},
    )

    assert decision.to_dict()["status"] == "warning"
    assert decision.to_json() == decision.to_json()
    assert "candidate:overall" in decision.to_text()


def test_experiment_regression_gate_passes_without_regressions() -> None:
    configs = (
        ExperimentConfig("routing-only", "Routing baseline.", "routing_only"),
        ExperimentConfig("routing-copy", "Same deterministic routing.", "routing_only"),
    )
    runner = ExperimentRunner(create_demo_benchmark_cases(), configs)
    _results, comparison = runner.run_and_compare()

    decision = ExperimentRegressionGate(ExperimentGateConfig()).evaluate(comparison)

    assert decision.status == "passed"
    assert decision.passed is True
    assert not decision.warning_metrics
    assert not decision.regressed_cases


def test_experiment_regression_gate_warns_in_warning_only_mode() -> None:
    comparison = create_demo_comparison()
    config = ExperimentGateConfig(
        overall_regression_threshold=0.03,
        routing_regression_threshold=0.03,
        context_regression_threshold=0.03,
        growth_regression_threshold=0.03,
        case_regression_threshold=0.05,
        warning_only=True,
    )

    decision = ExperimentRegressionGate(config).evaluate(comparison)

    assert decision.status == "warning"
    assert decision.passed is True
    assert decision.warning_only is True
    assert any(metric.endswith(":overall") for metric in decision.warning_metrics)
    assert decision.regressed_cases


def test_experiment_regression_gate_fails_in_strict_mode() -> None:
    comparison = create_demo_comparison()
    config = ExperimentGateConfig(
        overall_regression_threshold=0.03,
        routing_regression_threshold=0.03,
        context_regression_threshold=0.03,
        growth_regression_threshold=0.03,
        case_regression_threshold=0.05,
        warning_only=False,
    )

    decision = ExperimentRegressionGate(config).evaluate(comparison)

    assert decision.status == "failed"
    assert decision.passed is False
    assert decision.failed_metrics
    assert decision.regressed_cases


def test_experiment_regression_gate_detects_missing_scores() -> None:
    comparison = create_demo_comparison()
    broken = ExperimentComparisonReport(
        baseline_config_name=comparison.baseline_config_name,
        candidate_config_names=("missing-candidate",),
        per_config_score_summary=comparison.per_config_score_summary,
        deltas_vs_baseline={},
        best_config_name=comparison.best_config_name,
        improved_configs=(),
        regressed_configs=(),
        per_case_comparison={
            "case-1": {"overall_scores": {comparison.baseline_config_name: 1.0}}
        },
        regression_reports=(),
        summary="broken comparison",
    )

    decision = ExperimentRegressionGate(ExperimentGateConfig()).evaluate(broken)

    assert decision.status == "warning"
    assert "missing-candidate:missing-deltas" in decision.warning_metrics
    assert "case-1:missing-candidate:missing" in decision.regressed_cases


def test_experiment_cli_demo_behavior() -> None:
    output = format_experiment_demo()

    assert "ExperimentRunner Grona-vs-monolith demo" in output
    assert "Configs run: 4" in output
    assert "Experiment comparison report" in output
    assert "Best config:" in output
    assert "JSON preview:" in output


def test_experiment_gate_cli_demo_behavior() -> None:
    output = format_experiment_gate_demo()

    assert "ExperimentRegressionGate demo" in output
    assert "Mode: warning-only" in output
    assert "Experiment regression gate decision" in output
    assert "Gate decision JSON:" in output


def test_entrypoint_routes_experiment_demo(capsys) -> None:
    status = entrypoint_main(("--experiment-demo",))
    output = capsys.readouterr().out

    assert status == 0
    assert "ExperimentRunner Grona-vs-monolith demo" in output


def test_entrypoint_routes_experiment_gate_demo(capsys) -> None:
    status = entrypoint_main(("--experiment-gate-demo",))
    output = capsys.readouterr().out

    assert status == 0
    assert "ExperimentRegressionGate demo" in output
