"""Persistent benchmark run snapshots and deterministic regression comparison."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from json import dumps, loads
from pathlib import Path

from .benchmarks import BenchmarkReport, BenchmarkResult

Metadata = dict[str, object]
JsonValue = object


@dataclass(frozen=True)
class BenchmarkRunRecord:
    """Durable metadata wrapper around one benchmark report snapshot."""

    run_id: str
    created_at: str
    config_name: str
    benchmark_report: BenchmarkReport
    metadata: Metadata = field(default_factory=dict)
    git_commit: str | None = None
    version: str = "1"

    def __init__(
        self,
        run_id: str,
        created_at: str,
        config_name: str,
        benchmark_report: BenchmarkReport,
        metadata: Mapping[str, object] | None = None,
        git_commit: str | None = None,
        version: str = "1",
    ) -> None:
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "config_name", config_name)
        object.__setattr__(self, "benchmark_report", benchmark_report)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        object.__setattr__(self, "git_commit", git_commit)
        object.__setattr__(self, "version", version)
        if not run_id:
            raise ValueError("benchmark run_id cannot be empty")
        if not created_at:
            raise ValueError("benchmark created_at cannot be empty")
        if not config_name:
            raise ValueError("benchmark config_name cannot be empty")
        if not version:
            raise ValueError("benchmark run version cannot be empty")

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize the run record to deterministic JSON-compatible data."""
        return {
            "version": self.version,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "config_name": self.config_name,
            "git_commit": self.git_commit,
            "metadata": json_compatible(self.metadata),
            "benchmark_report": benchmark_report_to_dict(self.benchmark_report),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "BenchmarkRunRecord":
        """Build a benchmark run record from JSON-compatible data."""
        report_data = required_mapping(data, "benchmark_report")
        return cls(
            run_id=required_str(data, "run_id"),
            created_at=required_str(data, "created_at"),
            config_name=required_str(data, "config_name"),
            benchmark_report=benchmark_report_from_dict(report_data),
            metadata=dict(optional_mapping(data, "metadata")),
            git_commit=optional_str(data, "git_commit"),
            version=required_str(data, "version"),
        )

    def to_json(self) -> str:
        """Serialize the run as stable JSON for files, logs, or snapshots."""
        return dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "BenchmarkRunRecord":
        """Deserialize a benchmark run record from JSON text."""
        data = loads(text)
        if not isinstance(data, Mapping):
            raise ValueError("benchmark run JSON must contain an object")
        return cls.from_dict(data)

    def to_text(self) -> str:
        """Format one run record for compact human-readable output."""
        commit = self.git_commit or "unknown"
        return "\n".join(
            (
                f"Run: {self.run_id}",
                f"Created: {self.created_at}",
                f"Config: {self.config_name}",
                f"Git commit: {commit}",
                f"Overall: {self.benchmark_report.average_overall_score:.2f}",
            )
        )


class BenchmarkRunStore:
    """Minimal interface for benchmark run snapshot stores."""

    def add(self, record: BenchmarkRunRecord) -> None:
        """Persist one benchmark run record."""
        raise NotImplementedError

    def list(self) -> tuple[BenchmarkRunRecord, ...]:
        """Return stored records in deterministic order."""
        raise NotImplementedError

    def count(self) -> int:
        """Return the number of stored records."""
        return len(self.list())

    def get(self, run_id: str) -> BenchmarkRunRecord | None:
        """Return one record by id, if present."""
        for record in self.list():
            if record.run_id == run_id:
                return record
        return None

    def clear(self) -> None:
        """Remove stored records."""
        raise NotImplementedError


class InMemoryBenchmarkRunStore(BenchmarkRunStore):
    """Deterministic in-memory benchmark run store for tests and demos."""

    def __init__(self, records: Sequence[BenchmarkRunRecord] = ()) -> None:
        self._records: dict[str, BenchmarkRunRecord] = {}
        for record in records:
            self.add(record)

    def add(self, record: BenchmarkRunRecord) -> None:
        """Store or replace one benchmark run record by run id."""
        self._records[record.run_id] = record

    def list(self) -> tuple[BenchmarkRunRecord, ...]:
        """Return stored records ordered by creation time and run id."""
        return tuple(sorted(self._records.values(), key=lambda record: record_order_key(record)))

    def clear(self) -> None:
        """Remove all in-memory run records."""
        self._records.clear()


class JsonlBenchmarkRunStore(BenchmarkRunStore):
    """Append-only JSONL benchmark run store for explicit local snapshot files."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def add(self, record: BenchmarkRunRecord) -> None:
        """Append one benchmark run record as a JSONL line."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as file:
            file.write(record.to_json())
            file.write("\n")

    def list(self) -> tuple[BenchmarkRunRecord, ...]:
        """Read all JSONL records and return them in deterministic order."""
        if not self.path.exists():
            return ()
        records: list[BenchmarkRunRecord] = []
        with self.path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    records.append(BenchmarkRunRecord.from_json(text))
                except ValueError as exc:
                    message = f"invalid benchmark JSONL record at line {line_number}: {exc}"
                    raise ValueError(message) from exc
        return tuple(sorted(records, key=lambda record: record_order_key(record)))

    def clear(self) -> None:
        """Clear the JSONL file, creating parent directories if needed."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")


@dataclass(frozen=True)
class BenchmarkRegressionReport:
    """Deterministic score delta between two benchmark run snapshots."""

    baseline_run_id: str
    candidate_run_id: str
    overall_score_delta: float
    routing_score_delta: float
    context_score_delta: float
    growth_score_delta: float
    per_case_score_deltas: dict[str, dict[str, float | str]]
    improved_cases: tuple[str, ...]
    regressed_cases: tuple[str, ...]
    unchanged_cases: tuple[str, ...]
    regression_threshold: float
    summary: str
    metadata: Metadata = field(default_factory=dict)

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize the regression report to JSON-compatible data."""
        return {
            "baseline_run_id": self.baseline_run_id,
            "candidate_run_id": self.candidate_run_id,
            "overall_score_delta": self.overall_score_delta,
            "routing_score_delta": self.routing_score_delta,
            "context_score_delta": self.context_score_delta,
            "growth_score_delta": self.growth_score_delta,
            "per_case_score_deltas": json_compatible(self.per_case_score_deltas),
            "improved_cases": list(self.improved_cases),
            "regressed_cases": list(self.regressed_cases),
            "unchanged_cases": list(self.unchanged_cases),
            "regression_threshold": self.regression_threshold,
            "summary": self.summary,
            "metadata": json_compatible(self.metadata),
        }

    def to_json(self) -> str:
        """Serialize the regression report as stable JSON."""
        return dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def to_text(self) -> str:
        """Format the regression report for console output."""
        lines = [
            "Benchmark regression report",
            f"Baseline: {self.baseline_run_id}",
            f"Candidate: {self.candidate_run_id}",
            (
                "Deltas: "
                f"routing={self.routing_score_delta:+.3f}, "
                f"context={self.context_score_delta:+.3f}, "
                f"growth={self.growth_score_delta:+.3f}, "
                f"overall={self.overall_score_delta:+.3f}"
            ),
            self.summary,
            "Cases:",
        ]
        for case_id in sorted(self.per_case_score_deltas):
            delta = self.per_case_score_deltas[case_id]
            lines.append(
                f"- {case_id}: overall={float(delta['overall']):+.3f}; "
                f"status={delta['status']}"
            )
        return "\n".join(lines)


def create_benchmark_run_record(
    report: BenchmarkReport,
    run_id: str,
    created_at: str = "1970-01-01T00:00:00+00:00",
    metadata: Mapping[str, object] | None = None,
    git_commit: str | None = None,
    version: str = "1",
) -> BenchmarkRunRecord:
    """Create a run record from an existing benchmark report."""
    return BenchmarkRunRecord(
        run_id=run_id,
        created_at=created_at,
        config_name=report.config_name,
        benchmark_report=report,
        metadata=metadata,
        git_commit=git_commit,
        version=version,
    )


def compare_benchmark_runs(
    baseline: BenchmarkRunRecord,
    candidate: BenchmarkRunRecord,
    regression_threshold: float = 0.05,
) -> BenchmarkRegressionReport:
    """Compare two benchmark snapshots without LLM judging or statistical claims."""
    if regression_threshold < 0:
        raise ValueError("regression_threshold cannot be negative")

    baseline_report = baseline.benchmark_report
    candidate_report = candidate.benchmark_report
    baseline_results = {result.case_id: result for result in baseline_report.results}
    candidate_results = {result.case_id: result for result in candidate_report.results}
    case_ids = sorted(set(baseline_results) | set(candidate_results))

    deltas: dict[str, dict[str, float | str]] = {}
    improved: list[str] = []
    regressed: list[str] = []
    unchanged: list[str] = []

    for case_id in case_ids:
        base = baseline_results.get(case_id)
        cand = candidate_results.get(case_id)
        case_delta = case_score_delta(base, cand)
        status = classify_case_delta(case_delta["overall"], regression_threshold, base, cand)
        deltas[case_id] = {**case_delta, "status": status}
        if status == "improved":
            improved.append(case_id)
        elif status == "regressed":
            regressed.append(case_id)
        else:
            unchanged.append(case_id)

    summary = (
        f"candidate improved {len(improved)} cases, regressed {len(regressed)} cases, "
        f"unchanged {len(unchanged)} cases versus baseline."
    )
    return BenchmarkRegressionReport(
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        overall_score_delta=score_delta(
            baseline_report.average_overall_score,
            candidate_report.average_overall_score,
        ),
        routing_score_delta=score_delta(
            baseline_report.average_routing_score,
            candidate_report.average_routing_score,
        ),
        context_score_delta=score_delta(
            baseline_report.average_context_score,
            candidate_report.average_context_score,
        ),
        growth_score_delta=score_delta(
            baseline_report.average_growth_score,
            candidate_report.average_growth_score,
        ),
        per_case_score_deltas=deltas,
        improved_cases=tuple(improved),
        regressed_cases=tuple(regressed),
        unchanged_cases=tuple(unchanged),
        regression_threshold=round(regression_threshold, 3),
        summary=summary,
        metadata={
            "baseline_config_name": baseline.config_name,
            "candidate_config_name": candidate.config_name,
            "case_count": len(case_ids),
        },
    )


def benchmark_result_to_dict(result: BenchmarkResult) -> dict[str, JsonValue]:
    """Serialize one benchmark result to JSON-compatible data."""
    return {
        "case_id": result.case_id,
        "config_name": result.config_name,
        "selected_modules": list(result.selected_modules),
        "selected_domains": list(result.selected_domains),
        "matched_expected_domains": list(result.matched_expected_domains),
        "matched_expected_modules": list(result.matched_expected_modules),
        "matched_keywords": list(result.matched_keywords),
        "routing_score": result.routing_score,
        "context_score": result.context_score,
        "growth_score": result.growth_score,
        "overall_score": result.overall_score,
        "summary": result.summary,
        "metadata": json_compatible(result.metadata),
    }


def benchmark_result_from_dict(data: Mapping[str, object]) -> BenchmarkResult:
    """Deserialize one benchmark result from JSON-compatible data."""
    return BenchmarkResult(
        case_id=required_str(data, "case_id"),
        config_name=required_str(data, "config_name"),
        selected_modules=string_tuple(data, "selected_modules"),
        selected_domains=string_tuple(data, "selected_domains"),
        matched_expected_domains=string_tuple(data, "matched_expected_domains"),
        matched_expected_modules=string_tuple(data, "matched_expected_modules"),
        matched_keywords=string_tuple(data, "matched_keywords"),
        routing_score=float(data.get("routing_score", 0.0)),
        context_score=float(data.get("context_score", 0.0)),
        growth_score=float(data.get("growth_score", 0.0)),
        overall_score=float(data.get("overall_score", 0.0)),
        summary=required_str(data, "summary"),
        metadata=dict(optional_mapping(data, "metadata")),
    )


def benchmark_report_to_dict(report: BenchmarkReport) -> dict[str, JsonValue]:
    """Serialize one benchmark report to JSON-compatible data."""
    return {
        "config_name": report.config_name,
        "results": [benchmark_result_to_dict(result) for result in report.results],
        "average_routing_score": report.average_routing_score,
        "average_context_score": report.average_context_score,
        "average_growth_score": report.average_growth_score,
        "average_overall_score": report.average_overall_score,
        "summary": report.summary,
        "metadata": json_compatible(report.metadata),
    }


def benchmark_report_from_dict(data: Mapping[str, object]) -> BenchmarkReport:
    """Deserialize one benchmark report from JSON-compatible data."""
    raw_results = data.get("results", ())
    if not isinstance(raw_results, Sequence) or isinstance(raw_results, str):
        raise ValueError("benchmark report results must be a sequence")
    results = tuple(benchmark_result_from_dict(required_mapping(result, "result")) for result in raw_results)
    return BenchmarkReport(
        config_name=required_str(data, "config_name"),
        results=results,
        average_routing_score=float(data.get("average_routing_score", 0.0)),
        average_context_score=float(data.get("average_context_score", 0.0)),
        average_growth_score=float(data.get("average_growth_score", 0.0)),
        average_overall_score=float(data.get("average_overall_score", 0.0)),
        summary=required_str(data, "summary"),
        metadata=dict(optional_mapping(data, "metadata")),
    )


def case_score_delta(
    baseline: BenchmarkResult | None,
    candidate: BenchmarkResult | None,
) -> dict[str, float]:
    """Return score deltas for one case, including missing-case handling."""
    return {
        "routing": score_delta(score_or_zero(baseline, "routing"), score_or_zero(candidate, "routing")),
        "context": score_delta(score_or_zero(baseline, "context"), score_or_zero(candidate, "context")),
        "growth": score_delta(score_or_zero(baseline, "growth"), score_or_zero(candidate, "growth")),
        "overall": score_delta(score_or_zero(baseline, "overall"), score_or_zero(candidate, "overall")),
    }


def classify_case_delta(
    overall_delta: float,
    regression_threshold: float,
    baseline: BenchmarkResult | None,
    candidate: BenchmarkResult | None,
) -> str:
    """Classify one case delta for compact regression reporting."""
    if baseline is None and candidate is not None:
        return "improved"
    if baseline is not None and candidate is None:
        return "regressed"
    if overall_delta >= regression_threshold:
        return "improved"
    if overall_delta <= -regression_threshold:
        return "regressed"
    return "unchanged"


def score_or_zero(result: BenchmarkResult | None, score_name: str) -> float:
    """Read a named score from a result, or zero for missing cases."""
    if result is None:
        return 0.0
    return float(getattr(result, f"{score_name}_score"))


def score_delta(baseline_score: float, candidate_score: float) -> float:
    """Return rounded candidate-minus-baseline score delta."""
    return round(candidate_score - baseline_score, 3)


def record_order_key(record: BenchmarkRunRecord) -> tuple[str, str]:
    """Return deterministic ordering key for run stores."""
    return (record.created_at, record.run_id)


def json_compatible(value: object) -> JsonValue:
    """Convert common Python values to deterministic JSON-compatible data."""
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        return {str(key): json_compatible(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [json_compatible(item) for item in value]
    return str(value)


def required_mapping(data: object, key: str) -> Mapping[str, object]:
    """Read a required mapping field or raise a clear error."""
    if isinstance(data, Mapping) and key in data:
        value = data[key]
    else:
        value = data
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object")
    return value


def optional_mapping(data: Mapping[str, object], key: str) -> Mapping[str, object]:
    """Read an optional mapping field."""
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object")
    return value


def required_str(data: Mapping[str, object], key: str) -> str:
    """Read a required string field."""
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def optional_str(data: Mapping[str, object], key: str) -> str | None:
    """Read an optional string field."""
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string or null")
    return value


def string_tuple(data: Mapping[str, object], key: str) -> tuple[str, ...]:
    """Read a JSON list of strings as a tuple."""
    value = data.get(key, ())
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise ValueError(f"{key} must be a sequence of strings")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must contain only strings")
    return tuple(value)
