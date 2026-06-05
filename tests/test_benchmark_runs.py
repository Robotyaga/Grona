from grona import (
    BenchmarkReport,
    BenchmarkResult,
    BenchmarkRunRecord,
    InMemoryBenchmarkRunStore,
    JsonlBenchmarkRunStore,
    benchmark_report_from_dict,
    benchmark_report_to_dict,
    compare_benchmark_runs,
    create_benchmark_run_record,
)
from grona.benchmark_regression_cli import format_benchmark_regression_demo
from grona.entrypoint import main as entrypoint_main


def make_result(case_id: str, overall: float) -> BenchmarkResult:
    return BenchmarkResult(
        case_id=case_id,
        config_name="demo",
        routing_score=overall,
        context_score=overall,
        growth_score=overall,
        overall_score=overall,
        summary=f"{case_id} summary",
    )


def make_report(name: str, *results: BenchmarkResult) -> BenchmarkReport:
    return BenchmarkReport(name, results, summary=f"{name} summary")


def make_record(run_id: str, report: BenchmarkReport) -> BenchmarkRunRecord:
    return create_benchmark_run_record(
        report,
        run_id=run_id,
        created_at=f"2026-01-01T00:00:0{run_id[-1]}+00:00",
        git_commit="abc123",
    )


def test_benchmark_run_record_json_round_trip() -> None:
    report = make_report("baseline", make_result("case-a", 0.5))
    record = make_record("run-1", report)

    restored = BenchmarkRunRecord.from_json(record.to_json())

    assert restored == record
    assert restored.to_json() == record.to_json()


def test_benchmark_report_serialization_round_trip() -> None:
    report = make_report("baseline", make_result("case-a", 0.5), make_result("case-b", 0.8))

    restored = benchmark_report_from_dict(benchmark_report_to_dict(report))

    assert restored == report
    assert restored.results[0].case_id == "case-a"


def test_in_memory_benchmark_run_store_orders_records() -> None:
    later = make_record("run-2", make_report("candidate", make_result("case-a", 0.7)))
    earlier = make_record("run-1", make_report("baseline", make_result("case-a", 0.5)))
    store = InMemoryBenchmarkRunStore((later, earlier))

    records = store.list()

    assert store.count() == 2
    assert [record.run_id for record in records] == ["run-1", "run-2"]
    assert store.get("run-2") == later
    assert store.get("missing") is None
    store.clear()
    assert store.count() == 0


def test_jsonl_benchmark_run_store_persists_records(tmp_path) -> None:
    path = tmp_path / "runs.jsonl"
    store = JsonlBenchmarkRunStore(path)
    first = make_record("run-1", make_report("baseline", make_result("case-a", 0.5)))
    second = make_record("run-2", make_report("candidate", make_result("case-a", 0.6)))

    store.add(second)
    store.add(first)

    records = store.list()
    assert store.count() == 2
    assert [record.run_id for record in records] == ["run-1", "run-2"]
    assert JsonlBenchmarkRunStore(path).get("run-1") == first
    store.clear()
    assert store.list() == ()


def test_compare_benchmark_runs_detects_improvements() -> None:
    baseline = make_record("run-1", make_report("baseline", make_result("case-a", 0.5)))
    candidate = make_record("run-2", make_report("candidate", make_result("case-a", 0.8)))

    report = compare_benchmark_runs(baseline, candidate, regression_threshold=0.05)

    assert report.overall_score_delta == 0.3
    assert report.improved_cases == ("case-a",)
    assert report.regressed_cases == ()
    assert report.per_case_score_deltas["case-a"]["status"] == "improved"


def test_compare_benchmark_runs_detects_regressions() -> None:
    baseline = make_record("run-1", make_report("baseline", make_result("case-a", 0.8)))
    candidate = make_record("run-2", make_report("candidate", make_result("case-a", 0.5)))

    report = compare_benchmark_runs(baseline, candidate, regression_threshold=0.05)

    assert report.overall_score_delta == -0.3
    assert report.regressed_cases == ("case-a",)
    assert report.improved_cases == ()


def test_compare_benchmark_runs_respects_unchanged_threshold() -> None:
    baseline = make_record("run-1", make_report("baseline", make_result("case-a", 0.5)))
    candidate = make_record("run-2", make_report("candidate", make_result("case-a", 0.52)))

    report = compare_benchmark_runs(baseline, candidate, regression_threshold=0.05)

    assert report.unchanged_cases == ("case-a",)
    assert report.to_json() == report.to_json()


def test_benchmark_regression_cli_demo_behavior() -> None:
    output = format_benchmark_regression_demo()

    assert "Benchmark regression snapshot demo" in output
    assert "Stored runs: 2" in output
    assert "Benchmark regression report" in output
    assert "JSON preview:" in output


def test_entrypoint_routes_benchmark_regression_demo(capsys) -> None:
    status = entrypoint_main(("--benchmark-regression-demo",))
    output = capsys.readouterr().out

    assert status == 0
    assert "Benchmark regression snapshot demo" in output
