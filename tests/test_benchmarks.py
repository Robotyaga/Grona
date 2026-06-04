from grona import (
    BenchmarkCase,
    BenchmarkReport,
    BenchmarkResult,
    BenchmarkRunConfig,
    BenchmarkSuite,
    create_demo_benchmark_cases,
    create_demo_benchmark_configs,
    domain_match_score,
    keyword_context_score,
    module_match_score,
)
from grona.benchmark_cli import format_benchmark_demo


def test_benchmark_case_creation() -> None:
    case = BenchmarkCase(
        "case:auto",
        "Diagnose engine overheating.",
        expected_domains=("automotive",),
        expected_modules=("automotive-diagnostics",),
        expected_keywords=("engine", "overheating"),
        workspace="automotive",
        metadata={"source": "test"},
    )

    assert case.id == "case:auto"
    assert case.expected_domains == ("automotive",)
    assert case.expected_modules == ("automotive-diagnostics",)
    assert case.metadata["source"] == "test"


def test_benchmark_run_config_creation() -> None:
    config = BenchmarkRunConfig(
        "enhanced",
        use_memory=True,
        use_demo_memory=True,
        use_dataset_seeds=True,
        use_grape_clusters=True,
        use_growth_engine=True,
        use_orchestrator=True,
        workspace="default",
    )

    assert config.name == "enhanced"
    assert config.use_memory is True
    assert config.use_dataset_seeds is True
    assert config.workspace == "default"


def test_benchmark_result_formatting() -> None:
    result = BenchmarkResult(
        "case:auto",
        "baseline",
        selected_modules=("automotive-diagnostics",),
        selected_domains=("automotive",),
        matched_expected_domains=("automotive",),
        matched_expected_modules=("automotive-diagnostics",),
        matched_keywords=("engine",),
        routing_score=1.0,
        context_score=0.5,
        growth_score=0.0,
    )

    text = result.to_text()

    assert "Case: case:auto" in text
    assert "Selected modules: automotive-diagnostics" in text
    assert "overall=" in text
    assert result.overall_score == 0.675


def test_benchmark_report_formatting() -> None:
    result = BenchmarkResult(
        "case:auto",
        "baseline",
        selected_modules=("automotive-diagnostics",),
        selected_domains=("automotive",),
        routing_score=1.0,
        context_score=0.5,
        growth_score=0.0,
    )
    report = BenchmarkReport("baseline", (result,))

    assert report.average_routing_score == 1.0
    assert report.average_context_score == 0.5
    assert "Benchmark report: baseline" in report.to_text()
    assert "| Case | Routing | Context | Growth | Overall | Summary |" in report.to_markdown()


def test_domain_module_and_keyword_scoring() -> None:
    assert domain_match_score(("code", "cybersecurity"), ("code",)) == 0.5
    assert module_match_score(("code-assistant",), ("code-assistant", "general-reasoning")) == 1.0
    assert keyword_context_score(("engine", "coolant"), "check engine coolant first") == 1.0
    assert keyword_context_score(("engine", "radiator"), "check engine coolant first") == 0.5


def test_benchmark_suite_returns_report() -> None:
    suite = BenchmarkSuite(create_demo_benchmark_cases())
    report = suite.run(BenchmarkRunConfig("baseline-routing"))

    assert report.config_name == "baseline-routing"
    assert len(report.results) == len(create_demo_benchmark_cases())
    assert 0.0 <= report.average_overall_score <= 1.0
    assert all(result.summary for result in report.results)


def test_demo_benchmark_cases_are_deterministic() -> None:
    first = create_demo_benchmark_cases()
    second = create_demo_benchmark_cases()

    assert first == second
    assert [case.id for case in first] == [
        "auto-overheating",
        "security-code-review",
        "media-video-workflow",
        "document-retrieval",
        "general-instruction-following",
    ]


def test_demo_benchmark_configs_are_deterministic() -> None:
    first = create_demo_benchmark_configs()
    second = create_demo_benchmark_configs()

    assert first == second
    assert [config.name for config in first] == [
        "baseline-routing",
        "orchestrated-demo-memory",
        "dataset-growth-demo",
    ]


def test_baseline_and_enhanced_configs_produce_valid_scores() -> None:
    suite = BenchmarkSuite(create_demo_benchmark_cases())
    baseline = suite.run(create_demo_benchmark_configs()[0])
    enhanced = suite.run(create_demo_benchmark_configs()[-1])

    assert 0.0 <= baseline.average_overall_score <= 1.0
    assert 0.0 <= enhanced.average_overall_score <= 1.0
    assert enhanced.average_growth_score > baseline.average_growth_score
    assert enhanced.average_overall_score >= baseline.average_overall_score


def test_benchmark_cli_demo_behavior() -> None:
    output = format_benchmark_demo()

    assert "BenchmarkSuite MVP demo" in output
    assert "Report: baseline-routing" in output
    assert "Report: dataset-growth-demo" in output
    assert "Comparison:" in output
    assert "enhanced overall" in output
