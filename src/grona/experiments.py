"""Deterministic experiment runner for Grona-vs-monolith prototype comparisons."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from json import dumps

from .benchmark_runs import (
    BenchmarkRegressionReport,
    BenchmarkRunRecord,
    compare_benchmark_runs,
    create_benchmark_run_record,
    json_compatible,
)
from .benchmarks import (
    BenchmarkCase,
    BenchmarkReport,
    BenchmarkResult,
    BenchmarkRunConfig,
    BenchmarkSuite,
    keyword_context_score,
    matched_keywords_in_text,
    overall_benchmark_score,
)

Metadata = dict[str, object]
JsonValue = object

EXPERIMENT_MODES = frozenset(
    (
        "routing_only",
        "orchestrated_context",
        "memory_context",
        "growth_trace",
        "monolith_stub",
    )
)
EXPERIMENT_GATE_STATUSES = frozenset(("passed", "warning", "failed"))
EXPERIMENT_GATE_METRICS = ("overall", "routing", "context", "growth")


@dataclass(frozen=True)
class ExperimentConfig:
    """One deterministic experiment configuration."""

    name: str
    description: str
    mode: str
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        description: str,
        mode: str,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "description", " ".join(description.split()))
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not name:
            raise ValueError("experiment config name cannot be empty")
        if not description:
            raise ValueError("experiment config description cannot be empty")
        if mode not in EXPERIMENT_MODES:
            valid = ", ".join(sorted(EXPERIMENT_MODES))
            raise ValueError(f"unsupported experiment mode: {mode}; expected one of {valid}")

    def to_benchmark_run_config(self) -> BenchmarkRunConfig:
        """Convert deterministic Grona modes into BenchmarkSuite run configs."""
        if self.mode == "routing_only":
            return BenchmarkRunConfig(self.name, metadata=self.benchmark_metadata())
        if self.mode == "orchestrated_context":
            return BenchmarkRunConfig(
                self.name,
                use_orchestrator=True,
                metadata=self.benchmark_metadata(),
            )
        if self.mode == "memory_context":
            return BenchmarkRunConfig(
                self.name,
                use_memory=True,
                use_demo_memory=True,
                use_orchestrator=True,
                metadata=self.benchmark_metadata(),
            )
        if self.mode == "growth_trace":
            return BenchmarkRunConfig(
                self.name,
                use_memory=True,
                use_demo_memory=True,
                use_dataset_seeds=True,
                use_grape_clusters=True,
                use_growth_engine=True,
                use_orchestrator=True,
                metadata=self.benchmark_metadata(),
            )
        raise ValueError("monolith_stub does not map to BenchmarkSuite routing config")

    def benchmark_metadata(self) -> Metadata:
        """Return metadata passed into benchmark configs."""
        return {
            "experiment_mode": self.mode,
            "experiment_description": self.description,
            **self.metadata,
        }


@dataclass(frozen=True)
class ExperimentResult:
    """Result of one experiment config run."""

    config: ExperimentConfig
    benchmark_run: BenchmarkRunRecord
    summary: str
    metadata: Metadata = field(default_factory=dict)

    @property
    def overall_score(self) -> float:
        """Return average overall score for the benchmark run."""
        return self.benchmark_run.benchmark_report.average_overall_score

    @property
    def routing_score(self) -> float:
        """Return average routing score for the benchmark run."""
        return self.benchmark_run.benchmark_report.average_routing_score

    @property
    def context_score(self) -> float:
        """Return average context score for the benchmark run."""
        return self.benchmark_run.benchmark_report.average_context_score

    @property
    def growth_score(self) -> float:
        """Return average growth score for the benchmark run."""
        return self.benchmark_run.benchmark_report.average_growth_score

    @property
    def case_count(self) -> int:
        """Return number of benchmark cases in the run."""
        return len(self.benchmark_run.benchmark_report.results)

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize the experiment result for debug output."""
        return {
            "case_count": self.case_count,
            "config_name": self.config.name,
            "context_score": self.context_score,
            "growth_score": self.growth_score,
            "metadata": json_compatible(self.metadata),
            "mode": self.config.mode,
            "overall_score": self.overall_score,
            "routing_score": self.routing_score,
            "run_id": self.benchmark_run.run_id,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class ExperimentComparisonReport:
    """Deterministic comparison of multiple experiment results against a baseline."""

    baseline_config_name: str
    candidate_config_names: tuple[str, ...]
    per_config_score_summary: dict[str, dict[str, float | int | str]]
    deltas_vs_baseline: dict[str, dict[str, float]]
    best_config_name: str
    improved_configs: tuple[str, ...]
    regressed_configs: tuple[str, ...]
    per_case_comparison: dict[str, dict[str, JsonValue]]
    regression_reports: tuple[BenchmarkRegressionReport, ...]
    summary: str
    metadata: Metadata = field(default_factory=dict)

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize the comparison report to JSON-compatible data."""
        return {
            "baseline_config_name": self.baseline_config_name,
            "best_config_name": self.best_config_name,
            "candidate_config_names": list(self.candidate_config_names),
            "deltas_vs_baseline": json_compatible(self.deltas_vs_baseline),
            "improved_configs": list(self.improved_configs),
            "metadata": json_compatible(self.metadata),
            "per_case_comparison": json_compatible(self.per_case_comparison),
            "per_config_score_summary": json_compatible(self.per_config_score_summary),
            "regressed_configs": list(self.regressed_configs),
            "regression_reports": [report.to_dict() for report in self.regression_reports],
            "summary": self.summary,
        }

    def to_json(self) -> str:
        """Serialize the comparison report as stable JSON."""
        return dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def to_text(self) -> str:
        """Format the comparison report for console output."""
        lines = [
            "Experiment comparison report",
            f"Baseline: {self.baseline_config_name}",
            f"Best config: {self.best_config_name}",
            self.summary,
            "",
            "Scores:",
        ]
        for config_name in sorted(self.per_config_score_summary):
            scores = self.per_config_score_summary[config_name]
            lines.append(
                f"- {config_name}: overall={float(scores['overall']):.3f}, "
                f"routing={float(scores['routing']):.3f}, "
                f"context={float(scores['context']):.3f}, "
                f"growth={float(scores['growth']):.3f}, mode={scores['mode']}"
            )
        lines.append("")
        lines.append("Deltas vs baseline:")
        for config_name in sorted(self.deltas_vs_baseline):
            deltas = self.deltas_vs_baseline[config_name]
            lines.append(
                f"- {config_name}: overall={deltas['overall']:+.3f}, "
                f"routing={deltas['routing']:+.3f}, "
                f"context={deltas['context']:+.3f}, "
                f"growth={deltas['growth']:+.3f}"
            )
        lines.append("")
        lines.append("Limitations: deterministic rubric only; no LLMs or real monolithic baseline.")
        return "\n".join(lines)


@dataclass(frozen=True)
class ExperimentGateConfig:
    """Threshold config for deterministic experiment regression gate decisions."""

    overall_regression_threshold: float = 0.05
    routing_regression_threshold: float = 0.05
    context_regression_threshold: float = 0.05
    growth_regression_threshold: float = 0.05
    case_regression_threshold: float = 0.10
    warning_only: bool = True
    fail_on_missing_scores: bool = True
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        overall_regression_threshold: float = 0.05,
        routing_regression_threshold: float = 0.05,
        context_regression_threshold: float = 0.05,
        growth_regression_threshold: float = 0.05,
        case_regression_threshold: float = 0.10,
        warning_only: bool = True,
        fail_on_missing_scores: bool = True,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        thresholds = {
            "overall_regression_threshold": overall_regression_threshold,
            "routing_regression_threshold": routing_regression_threshold,
            "context_regression_threshold": context_regression_threshold,
            "growth_regression_threshold": growth_regression_threshold,
            "case_regression_threshold": case_regression_threshold,
        }
        for name, value in thresholds.items():
            if value < 0:
                raise ValueError(f"{name} cannot be negative")
        object.__setattr__(self, "overall_regression_threshold", overall_regression_threshold)
        object.__setattr__(self, "routing_regression_threshold", routing_regression_threshold)
        object.__setattr__(self, "context_regression_threshold", context_regression_threshold)
        object.__setattr__(self, "growth_regression_threshold", growth_regression_threshold)
        object.__setattr__(self, "case_regression_threshold", case_regression_threshold)
        object.__setattr__(self, "warning_only", warning_only)
        object.__setattr__(self, "fail_on_missing_scores", fail_on_missing_scores)
        object.__setattr__(self, "metadata", dict(metadata or {}))

    def threshold_for_metric(self, metric: str) -> float:
        """Return the configured regression threshold for one aggregate metric."""
        thresholds = {
            "overall": self.overall_regression_threshold,
            "routing": self.routing_regression_threshold,
            "context": self.context_regression_threshold,
            "growth": self.growth_regression_threshold,
        }
        if metric not in thresholds:
            raise ValueError(f"unsupported experiment gate metric: {metric}")
        return thresholds[metric]

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize gate config to deterministic JSON-compatible data."""
        return {
            "case_regression_threshold": self.case_regression_threshold,
            "context_regression_threshold": self.context_regression_threshold,
            "fail_on_missing_scores": self.fail_on_missing_scores,
            "growth_regression_threshold": self.growth_regression_threshold,
            "metadata": json_compatible(self.metadata),
            "overall_regression_threshold": self.overall_regression_threshold,
            "routing_regression_threshold": self.routing_regression_threshold,
            "warning_only": self.warning_only,
        }

    def to_json(self) -> str:
        """Serialize gate config as stable JSON."""
        return dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class ExperimentGateDecision:
    """Explainable deterministic decision returned by ExperimentRegressionGate."""

    passed: bool
    warning_only: bool
    status: str
    reasons: tuple[str, ...]
    failed_metrics: tuple[str, ...] = ()
    warning_metrics: tuple[str, ...] = ()
    regressed_cases: tuple[str, ...] = ()
    summary: str = ""
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        passed: bool,
        warning_only: bool,
        status: str,
        reasons: Sequence[str] = (),
        failed_metrics: Sequence[str] = (),
        warning_metrics: Sequence[str] = (),
        regressed_cases: Sequence[str] = (),
        summary: str = "",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if status not in EXPERIMENT_GATE_STATUSES:
            valid = ", ".join(sorted(EXPERIMENT_GATE_STATUSES))
            message = (
                f"unsupported experiment gate status: {status}; "
                f"expected one of {valid}"
            )
            raise ValueError(message)
        object.__setattr__(self, "passed", passed)
        object.__setattr__(self, "warning_only", warning_only)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "reasons", tuple(reasons))
        object.__setattr__(self, "failed_metrics", tuple(failed_metrics))
        object.__setattr__(self, "warning_metrics", tuple(warning_metrics))
        object.__setattr__(self, "regressed_cases", tuple(regressed_cases))
        object.__setattr__(self, "summary", summary)
        object.__setattr__(self, "metadata", dict(metadata or {}))

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize the gate decision to deterministic JSON-compatible data."""
        return {
            "failed_metrics": list(self.failed_metrics),
            "metadata": json_compatible(self.metadata),
            "passed": self.passed,
            "reasons": list(self.reasons),
            "regressed_cases": list(self.regressed_cases),
            "status": self.status,
            "summary": self.summary,
            "warning_metrics": list(self.warning_metrics),
            "warning_only": self.warning_only,
        }

    def to_json(self) -> str:
        """Serialize the gate decision as stable JSON."""
        return dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def to_text(self) -> str:
        """Format the gate decision for console output."""
        lines = [
            "Experiment regression gate decision",
            f"Status: {self.status}",
            f"Passed: {self.passed}",
            f"Warning only: {self.warning_only}",
            self.summary,
        ]
        if self.warning_metrics:
            lines.append("Warning metrics:")
            lines.extend(f"- {metric}" for metric in self.warning_metrics)
        if self.failed_metrics:
            lines.append("Failed metrics:")
            lines.extend(f"- {metric}" for metric in self.failed_metrics)
        if self.regressed_cases:
            lines.append("Regressed cases:")
            lines.extend(f"- {case}" for case in self.regressed_cases)
        if self.reasons:
            lines.append("Reasons:")
            lines.extend(f"- {reason}" for reason in self.reasons)
        lines.append("Limitations: deterministic thresholds only; no LLM judging or quality proof.")
        return "\n".join(line for line in lines if line)


class ExperimentRegressionGate:
    """Evaluate an experiment comparison report against deterministic thresholds."""

    def __init__(self, config: ExperimentGateConfig | None = None) -> None:
        self.config = config or ExperimentGateConfig()

    def evaluate(self, comparison: ExperimentComparisonReport) -> ExperimentGateDecision:
        """Return an explainable gate decision for one experiment comparison report."""
        metric_regressions = self._metric_regressions(comparison)
        case_regressions = self._case_regressions(comparison)
        reasons = tuple(
            sorted(
                (
                    *(regression["reason"] for regression in metric_regressions),
                    *(regression["reason"] for regression in case_regressions),
                )
            )
        )
        regressed_cases = tuple(
            sorted(str(regression["label"]) for regression in case_regressions)
        )
        metric_labels = tuple(sorted(str(regression["label"]) for regression in metric_regressions))
        has_regression = bool(metric_labels or regressed_cases)
        if not has_regression:
            return ExperimentGateDecision(
                passed=True,
                warning_only=self.config.warning_only,
                status="passed",
                reasons=("no experiment regression exceeded configured thresholds",),
                summary="experiment regression gate passed",
                metadata=self._decision_metadata(comparison, metric_regressions, case_regressions),
            )
        if self.config.warning_only:
            return ExperimentGateDecision(
                passed=True,
                warning_only=True,
                status="warning",
                reasons=reasons,
                warning_metrics=metric_labels,
                regressed_cases=regressed_cases,
                summary="experiment regression gate produced warnings only",
                metadata=self._decision_metadata(comparison, metric_regressions, case_regressions),
            )
        return ExperimentGateDecision(
            passed=False,
            warning_only=False,
            status="failed",
            reasons=reasons,
            failed_metrics=metric_labels,
            regressed_cases=regressed_cases,
            summary="experiment regression gate failed configured thresholds",
            metadata=self._decision_metadata(comparison, metric_regressions, case_regressions),
        )

    def _metric_regressions(
        self,
        comparison: ExperimentComparisonReport,
    ) -> tuple[dict[str, JsonValue], ...]:
        regressions: list[dict[str, JsonValue]] = []
        for config_name in sorted(comparison.candidate_config_names):
            deltas = comparison.deltas_vs_baseline.get(config_name)
            if deltas is None:
                if self.config.fail_on_missing_scores:
                    regressions.append(
                        {
                            "label": f"{config_name}:missing-deltas",
                            "reason": f"{config_name} is missing aggregate score deltas",
                        }
                    )
                continue
            for metric in EXPERIMENT_GATE_METRICS:
                threshold = self.config.threshold_for_metric(metric)
                if metric not in deltas:
                    if self.config.fail_on_missing_scores:
                        regressions.append(
                            {
                                "label": f"{config_name}:{metric}:missing",
                                "reason": f"{config_name} is missing {metric} delta",
                            }
                        )
                    continue
                delta = deltas[metric]
                if delta <= -threshold:
                    regressions.append(
                        {
                            "delta": delta,
                            "label": f"{config_name}:{metric}",
                            "reason": (
                                f"{config_name} {metric} delta {delta:+.3f} "
                                f"exceeded regression threshold {-threshold:+.3f}"
                            ),
                            "threshold": threshold,
                        }
                    )
        return tuple(regressions)

    def _case_regressions(
        self,
        comparison: ExperimentComparisonReport,
    ) -> tuple[dict[str, JsonValue], ...]:
        regressions: list[dict[str, JsonValue]] = []
        baseline_name = comparison.baseline_config_name
        threshold = comparison.metadata.get(
            "case_regression_threshold",
            self.config.case_regression_threshold,
        )
        threshold = float(threshold)
        for case_id, case_data in sorted(comparison.per_case_comparison.items()):
            raw_scores = case_data.get("overall_scores")
            scores = raw_scores if isinstance(raw_scores, Mapping) else {}
            baseline_score = scores.get(baseline_name)
            if baseline_score is None:
                if self.config.fail_on_missing_scores:
                    regressions.append(
                        {
                            "label": f"{case_id}:{baseline_name}:missing",
                            "reason": (
                                f"case {case_id} is missing baseline score "
                                f"for {baseline_name}"
                            ),
                        }
                    )
                continue
            for config_name in sorted(comparison.candidate_config_names):
                candidate_score = scores.get(config_name)
                if candidate_score is None:
                    if self.config.fail_on_missing_scores:
                        regressions.append(
                            {
                                "label": f"{case_id}:{config_name}:missing",
                                "reason": (
                                    f"case {case_id} is missing candidate score "
                                    f"for {config_name}"
                                ),
                            }
                        )
                    continue
                delta = float(candidate_score) - float(baseline_score)
                if delta <= -threshold:
                    regressions.append(
                        {
                            "case_id": case_id,
                            "delta": delta,
                            "label": f"{case_id}:{config_name}",
                            "reason": (
                                f"case {case_id} candidate {config_name} delta {delta:+.3f} "
                                f"exceeded case regression threshold {-threshold:+.3f}"
                            ),
                            "threshold": threshold,
                        }
                    )
        return tuple(regressions)

    def _decision_metadata(
        self,
        comparison: ExperimentComparisonReport,
        metric_regressions: Sequence[Mapping[str, JsonValue]],
        case_regressions: Sequence[Mapping[str, JsonValue]],
    ) -> Metadata:
        return {
            "baseline_config_name": comparison.baseline_config_name,
            "candidate_config_names": list(comparison.candidate_config_names),
            "case_regression_count": len(case_regressions),
            "config": self.config.to_dict(),
            "metric_regression_count": len(metric_regressions),
        }


class ExperimentRunner:
    """Run deterministic experiment configs and compare them against a baseline."""

    def __init__(
        self,
        cases: Sequence[BenchmarkCase],
        configs: Sequence[ExperimentConfig],
        baseline_config_name: str | None = None,
        regression_threshold: float = 0.05,
    ) -> None:
        self.cases = tuple(cases)
        self.configs = tuple(configs)
        if not self.cases:
            raise ValueError("experiment runner requires at least one benchmark case")
        if not self.configs:
            raise ValueError("experiment runner requires at least one experiment config")
        self.baseline_config_name = baseline_config_name or self.configs[0].name
        self.regression_threshold = regression_threshold
        if regression_threshold < 0:
            raise ValueError("regression_threshold cannot be negative")
        if self.baseline_config_name not in {config.name for config in self.configs}:
            raise ValueError("baseline config must exist in experiment configs")

    def run(self) -> tuple[ExperimentResult, ...]:
        """Run every experiment config and return deterministic results."""
        suite = BenchmarkSuite(self.cases)
        results: list[ExperimentResult] = []
        for index, config in enumerate(self.configs):
            report = self.run_config(suite, config)
            run = create_benchmark_run_record(
                report,
                run_id=f"experiment-{index + 1:03d}-{config.name}",
                created_at=f"2026-01-01T00:{index:02d}:00+00:00",
                metadata={
                    "experiment_description": config.description,
                    "experiment_mode": config.mode,
                },
            )
            results.append(
                ExperimentResult(
                    config=config,
                    benchmark_run=run,
                    summary=summarize_experiment_result(config, report),
                    metadata={"result_index": index},
                )
            )
        return tuple(results)

    def run_config(self, suite: BenchmarkSuite, config: ExperimentConfig) -> BenchmarkReport:
        """Run one experiment config through BenchmarkSuite or the monolith stub."""
        if config.mode == "monolith_stub":
            return MonolithBaseline(config.name).run(self.cases)
        return suite.run(config.to_benchmark_run_config())

    def compare(self, results: Sequence[ExperimentResult]) -> ExperimentComparisonReport:
        """Compare experiment results against the configured baseline."""
        result_tuple = tuple(results)
        if not result_tuple:
            raise ValueError("cannot compare empty experiment results")
        by_name = {result.config.name: result for result in result_tuple}
        baseline = by_name[self.baseline_config_name]
        candidates = tuple(result for result in result_tuple if result is not baseline)
        regression_reports = tuple(
            compare_benchmark_runs(
                baseline.benchmark_run,
                candidate.benchmark_run,
                regression_threshold=self.regression_threshold,
            )
            for candidate in candidates
        )
        deltas = {
            report.metadata["candidate_config_name"]: {
                "context": report.context_score_delta,
                "growth": report.growth_score_delta,
                "overall": report.overall_score_delta,
                "routing": report.routing_score_delta,
            }
            for report in regression_reports
        }
        improved_names = (
            name
            for name, delta in deltas.items()
            if delta["overall"] >= self.regression_threshold
        )
        regressed_names = (
            name
            for name, delta in deltas.items()
            if delta["overall"] <= -self.regression_threshold
        )
        improved = tuple(sorted(improved_names))
        regressed = tuple(sorted(regressed_names))
        best = best_experiment_result(result_tuple)
        summary = (
            f"ran {len(result_tuple)} deterministic experiment configs; "
            f"best overall config is {best.config.name}."
        )
        return ExperimentComparisonReport(
            baseline_config_name=baseline.config.name,
            candidate_config_names=tuple(sorted(result.config.name for result in candidates)),
            per_config_score_summary=per_config_score_summary(result_tuple),
            deltas_vs_baseline=deltas,
            best_config_name=best.config.name,
            improved_configs=improved,
            regressed_configs=regressed,
            per_case_comparison=per_case_comparison(result_tuple),
            regression_reports=regression_reports,
            summary=summary,
            metadata={
                "regression_threshold": self.regression_threshold,
                "result_count": len(result_tuple),
            },
        )

    def run_and_compare(self) -> tuple[tuple[ExperimentResult, ...], ExperimentComparisonReport]:
        """Run all configs and return results plus comparison report."""
        results = self.run()
        return results, self.compare(results)


class MonolithBaseline:
    """Deterministic broad baseline stub; not a real monolithic LLM."""

    def __init__(self, config_name: str = "monolith-stub") -> None:
        self.config_name = config_name

    def run(self, cases: Sequence[BenchmarkCase]) -> BenchmarkReport:
        """Return a deterministic report with weak broad coverage and no real model calls."""
        results = tuple(self.run_case(case) for case in cases)
        return BenchmarkReport(
            self.config_name,
            results,
            summary=f"{self.config_name} ran as a deterministic monolith stub.",
            metadata={
                "case_count": len(results),
                "experiment_mode": "monolith_stub",
                "limitations": "not a real monolithic LLM baseline",
            },
        )

    def run_case(self, case: BenchmarkCase) -> BenchmarkResult:
        """Score one case with broad weak deterministic behavior."""
        matched_keywords = matched_keywords_in_text(case.expected_keywords, case.task)
        context = round(keyword_context_score(case.expected_keywords, case.task) * 0.45, 3)
        routing = 0.2 if "general" not in case.expected_domains else 0.45
        growth = 0.0
        return BenchmarkResult(
            case_id=case.id,
            config_name=self.config_name,
            selected_modules=("monolith-stub",),
            selected_domains=("general",),
            matched_expected_domains=("general",) if "general" in case.expected_domains else (),
            matched_expected_modules=(),
            matched_keywords=matched_keywords,
            routing_score=routing,
            context_score=context,
            growth_score=growth,
            overall_score=overall_benchmark_score(routing, context, growth),
            summary="deterministic broad baseline without explicit module/context trace",
            metadata={
                "expected_domain_count": len(case.expected_domains),
                "expected_module_count": len(case.expected_modules),
                "monolith_stub": True,
            },
        )


def create_demo_experiment_configs() -> tuple[ExperimentConfig, ...]:
    """Create deterministic configs for the experiment demo."""
    return (
        ExperimentConfig(
            "routing-only",
            "Baseline Grona routing without memory or growth traces.",
            "routing_only",
        ),
        ExperimentConfig(
            "memory-context",
            "Grona routing with deterministic demo memory and orchestration.",
            "memory_context",
        ),
        ExperimentConfig(
            "growth-trace",
            "Grona routing with deterministic dataset seeds, grape clusters, and GrowthEngine.",
            "growth_trace",
        ),
        ExperimentConfig(
            "monolith-stub",
            "Deterministic broad monolith stub without real model calls.",
            "monolith_stub",
        ),
    )


def summarize_experiment_result(config: ExperimentConfig, report: BenchmarkReport) -> str:
    """Create a compact deterministic result summary."""
    return (
        f"{config.name} ({config.mode}) ran {len(report.results)} cases "
        f"with overall={report.average_overall_score:.3f}."
    )


def per_config_score_summary(
    results: Sequence[ExperimentResult],
) -> dict[str, dict[str, float | int | str]]:
    """Return compact score summary by config name."""
    return {
        result.config.name: {
            "case_count": result.case_count,
            "context": result.context_score,
            "growth": result.growth_score,
            "mode": result.config.mode,
            "overall": result.overall_score,
            "routing": result.routing_score,
        }
        for result in sorted(results, key=lambda item: item.config.name)
    }


def per_case_comparison(results: Sequence[ExperimentResult]) -> dict[str, dict[str, JsonValue]]:
    """Return per-case score summaries across configs."""
    config_scores: dict[str, dict[str, float]] = {}
    for result in results:
        for benchmark_result in result.benchmark_run.benchmark_report.results:
            config_scores.setdefault(benchmark_result.case_id, {})[
                result.config.name
            ] = benchmark_result.overall_score
    comparison: dict[str, dict[str, JsonValue]] = {}
    for case_id, scores in sorted(config_scores.items()):
        best_name = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[0][0]
        comparison[case_id] = {
            "best_config": best_name,
            "overall_scores": dict(sorted(scores.items())),
        }
    return comparison


def best_experiment_result(results: Sequence[ExperimentResult]) -> ExperimentResult:
    """Return the highest overall result with deterministic name tie-break."""
    return sorted(results, key=lambda result: (-result.overall_score, result.config.name))[0]
