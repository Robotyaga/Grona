"""Deterministic benchmark helpers for Grona prototype comparisons."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .context import ContextBuilder, ContextItem
from .datasets import (
    create_demo_alpaca_samples,
    create_demo_sharegpt_samples,
    knowledge_seeds_from_dataset_samples,
)
from .defaults import create_default_registry
from .growth import KnowledgeSeed
from .growth_clusters import GrapeCluster, GrapeClusterer, memory_records_from_grape_clusters
from .growth_engine import GrowthEngine, GrowthPlan, memory_records_from_growth_plan
from .growth_review import KnowledgeReviewPipeline, SeedReviewDecision
from .memory import InMemoryKeywordMemory, MemoryModule, MemoryRecord, create_default_memory_modules
from .orchestrator import Orchestrator
from .registry import ModuleRegistry
from .router import Router, tokenize
from .workspace import filter_modules_for_workspace, get_builtin_workspace_profile

Metadata = dict[str, object]

MODULE_DOMAIN_LABELS = {
    "code-assistant": "code",
    "automotive-diagnostics": "automotive",
    "cybersecurity-scanner": "cybersecurity",
    "media-video-tool": "media",
    "document-search": "document",
    "general-reasoning": "general",
}


@dataclass(frozen=True)
class BenchmarkCase:
    """One deterministic task Grona should route or orchestrate."""

    id: str
    task: str
    expected_domains: tuple[str, ...] = ()
    expected_modules: tuple[str, ...] = ()
    expected_keywords: tuple[str, ...] = ()
    workspace: str = "default"
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        id: str,
        task: str,
        expected_domains: Sequence[str] = (),
        expected_modules: Sequence[str] = (),
        expected_keywords: Sequence[str] = (),
        workspace: str = "default",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "task", " ".join(task.split()))
        object.__setattr__(self, "expected_domains", tuple(expected_domains))
        object.__setattr__(self, "expected_modules", tuple(expected_modules))
        object.__setattr__(self, "expected_keywords", tuple(expected_keywords))
        object.__setattr__(self, "workspace", workspace)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not id:
            raise ValueError("benchmark case id cannot be empty")
        if not task:
            raise ValueError("benchmark case task cannot be empty")


@dataclass(frozen=True)
class BenchmarkRunConfig:
    """Deterministic switches for one benchmark run."""

    name: str
    use_memory: bool = False
    use_demo_memory: bool = False
    use_dataset_seeds: bool = False
    use_grape_clusters: bool = False
    use_growth_engine: bool = False
    use_orchestrator: bool = False
    workspace: str | None = None
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        use_memory: bool = False,
        use_demo_memory: bool = False,
        use_dataset_seeds: bool = False,
        use_grape_clusters: bool = False,
        use_growth_engine: bool = False,
        use_orchestrator: bool = False,
        workspace: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "use_memory", use_memory)
        object.__setattr__(self, "use_demo_memory", use_demo_memory)
        object.__setattr__(self, "use_dataset_seeds", use_dataset_seeds)
        object.__setattr__(self, "use_grape_clusters", use_grape_clusters)
        object.__setattr__(self, "use_growth_engine", use_growth_engine)
        object.__setattr__(self, "use_orchestrator", use_orchestrator)
        object.__setattr__(self, "workspace", workspace)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not name:
            raise ValueError("benchmark config name cannot be empty")


@dataclass(frozen=True)
class BenchmarkResult:
    """Score and trace for one benchmark case under one run config."""

    case_id: str
    config_name: str
    selected_modules: tuple[str, ...]
    selected_domains: tuple[str, ...]
    matched_expected_domains: tuple[str, ...]
    matched_expected_modules: tuple[str, ...]
    matched_keywords: tuple[str, ...]
    routing_score: float
    context_score: float
    growth_score: float
    overall_score: float
    summary: str
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        case_id: str,
        config_name: str,
        selected_modules: Sequence[str] = (),
        selected_domains: Sequence[str] = (),
        matched_expected_domains: Sequence[str] = (),
        matched_expected_modules: Sequence[str] = (),
        matched_keywords: Sequence[str] = (),
        routing_score: float = 0.0,
        context_score: float = 0.0,
        growth_score: float = 0.0,
        overall_score: float | None = None,
        summary: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        calculated = overall_score
        if calculated is None:
            calculated = overall_benchmark_score(routing_score, context_score, growth_score)
        object.__setattr__(self, "case_id", case_id)
        object.__setattr__(self, "config_name", config_name)
        object.__setattr__(self, "selected_modules", tuple(selected_modules))
        object.__setattr__(self, "selected_domains", tuple(selected_domains))
        object.__setattr__(self, "matched_expected_domains", tuple(matched_expected_domains))
        object.__setattr__(self, "matched_expected_modules", tuple(matched_expected_modules))
        object.__setattr__(self, "matched_keywords", tuple(matched_keywords))
        object.__setattr__(self, "routing_score", clamp_score(routing_score))
        object.__setattr__(self, "context_score", clamp_score(context_score))
        object.__setattr__(self, "growth_score", clamp_score(growth_score))
        object.__setattr__(self, "overall_score", clamp_score(calculated))
        object.__setattr__(self, "summary", summary or summarize_result(self))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not case_id:
            raise ValueError("benchmark result case_id cannot be empty")
        if not config_name:
            raise ValueError("benchmark result config_name cannot be empty")

    def to_text(self) -> str:
        """Format one result for compact human-readable reports."""
        modules = ", ".join(self.selected_modules) or "none"
        domains = ", ".join(self.selected_domains) or "none"
        keywords = ", ".join(self.matched_keywords) or "none"
        return "\n".join(
            (
                f"Case: {self.case_id}",
                f"Config: {self.config_name}",
                f"Selected modules: {modules}",
                f"Selected domains: {domains}",
                f"Matched keywords: {keywords}",
                (
                    "Scores: "
                    f"routing={self.routing_score:.2f}, "
                    f"context={self.context_score:.2f}, "
                    f"growth={self.growth_score:.2f}, "
                    f"overall={self.overall_score:.2f}"
                ),
                f"Summary: {self.summary}",
            )
        )


@dataclass(frozen=True)
class BenchmarkReport:
    """Aggregate benchmark results for one run config."""

    config_name: str
    results: tuple[BenchmarkResult, ...]
    average_routing_score: float
    average_context_score: float
    average_growth_score: float
    average_overall_score: float
    summary: str
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        config_name: str,
        results: Sequence[BenchmarkResult] = (),
        average_routing_score: float | None = None,
        average_context_score: float | None = None,
        average_growth_score: float | None = None,
        average_overall_score: float | None = None,
        summary: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        result_tuple = tuple(results)
        object.__setattr__(self, "config_name", config_name)
        object.__setattr__(self, "results", result_tuple)
        object.__setattr__(
            self,
            "average_routing_score",
            clamp_score(average_routing_score if average_routing_score is not None else average_score(r.routing_score for r in result_tuple)),
        )
        object.__setattr__(
            self,
            "average_context_score",
            clamp_score(average_context_score if average_context_score is not None else average_score(r.context_score for r in result_tuple)),
        )
        object.__setattr__(
            self,
            "average_growth_score",
            clamp_score(average_growth_score if average_growth_score is not None else average_score(r.growth_score for r in result_tuple)),
        )
        object.__setattr__(
            self,
            "average_overall_score",
            clamp_score(average_overall_score if average_overall_score is not None else average_score(r.overall_score for r in result_tuple)),
        )
        object.__setattr__(self, "summary", summary or summarize_report(config_name, result_tuple))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not config_name:
            raise ValueError("benchmark report config_name cannot be empty")

    def to_text(self) -> str:
        """Format the report as a compact text block."""
        lines = [
            f"Benchmark report: {self.config_name}",
            self.summary,
            (
                "Averages: "
                f"routing={self.average_routing_score:.2f}, "
                f"context={self.average_context_score:.2f}, "
                f"growth={self.average_growth_score:.2f}, "
                f"overall={self.average_overall_score:.2f}"
            ),
            "",
            "Results:",
        ]
        if not self.results:
            lines.append("- none")
            return "\n".join(lines)
        for result in self.results:
            lines.append(result.to_text())
            lines.append("")
        return "\n".join(lines).rstrip()

    def to_markdown(self) -> str:
        """Format the report as a small markdown table."""
        lines = [
            f"# Benchmark report: {self.config_name}",
            "",
            self.summary,
            "",
            "| Case | Routing | Context | Growth | Overall | Summary |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
        for result in self.results:
            lines.append(
                "| "
                f"{result.case_id} | "
                f"{result.routing_score:.2f} | "
                f"{result.context_score:.2f} | "
                f"{result.growth_score:.2f} | "
                f"{result.overall_score:.2f} | "
                f"{result.summary} |"
            )
        return "\n".join(lines)


class BenchmarkSuite:
    """Run deterministic Grona benchmark cases with local mock components only."""

    def __init__(
        self,
        cases: Sequence[BenchmarkCase],
        registry: ModuleRegistry | None = None,
    ) -> None:
        self.cases = tuple(cases)
        self.registry = registry or create_default_registry()

    def run(self, config: BenchmarkRunConfig) -> BenchmarkReport:
        """Run all cases and return an aggregate report."""
        results = tuple(self._run_case(case, config) for case in self.cases)
        return BenchmarkReport(
            config.name,
            results,
            metadata={
                "case_count": len(self.cases),
                "use_memory": config.use_memory,
                "use_dataset_seeds": config.use_dataset_seeds,
                "use_grape_clusters": config.use_grape_clusters,
                "use_growth_engine": config.use_growth_engine,
                "use_orchestrator": config.use_orchestrator,
            },
        )

    def _run_case(self, case: BenchmarkCase, config: BenchmarkRunConfig) -> BenchmarkResult:
        workspace_name = config.workspace or case.workspace or "default"
        profile = get_builtin_workspace_profile(workspace_name)
        registry = filter_modules_for_workspace(self.registry, profile)
        router = Router(registry)
        memory_modules, growth_plan, clusters = build_benchmark_memory(config)
        context_builder = ContextBuilder(memory_modules=memory_modules)

        if config.use_orchestrator:
            orchestration = Orchestrator(router, context_builder=context_builder).run(case.task)
            decision = orchestration.routing_decision
            context_items = orchestration.context_items
        else:
            decision = router.route(case.task)
            context_items = context_builder.build(decision, case.task)

        selected_modules = decision.selected_names
        selected_domains = selected_domain_labels(selected_modules)
        matched_domains = matched_values(case.expected_domains, selected_domains)
        matched_modules = matched_values(case.expected_modules, selected_modules)
        context_text = benchmark_context_text(case, context_items, growth_plan, clusters)
        matched_keywords = matched_keywords_in_text(case.expected_keywords, context_text)
        routing = routing_match_score(case.expected_domains, selected_domains, case.expected_modules, selected_modules)
        context = keyword_context_score(case.expected_keywords, context_text)
        growth = growth_decision_score(case.expected_domains, case.expected_keywords, growth_plan, clusters)
        overall = overall_benchmark_score(routing, context, growth)
        return BenchmarkResult(
            case_id=case.id,
            config_name=config.name,
            selected_modules=selected_modules,
            selected_domains=selected_domains,
            matched_expected_domains=matched_domains,
            matched_expected_modules=matched_modules,
            matched_keywords=matched_keywords,
            routing_score=routing,
            context_score=context,
            growth_score=growth,
            overall_score=overall,
            metadata={
                "workspace": workspace_name,
                "context_count": len(context_items),
                "growth_decision_count": len(growth_plan.decisions) if growth_plan else 0,
                "cluster_count": len(clusters),
            },
        )


def build_benchmark_memory(
    config: BenchmarkRunConfig,
) -> tuple[tuple[MemoryModule, ...], GrowthPlan | None, tuple[GrapeCluster, ...]]:
    """Build deterministic memory modules requested by a benchmark config."""
    memory_modules: list[MemoryModule] = []
    if config.use_memory or config.use_demo_memory:
        memory_modules.extend(create_default_memory_modules())

    seeds: tuple[KnowledgeSeed, ...] = ()
    if config.use_dataset_seeds:
        dataset_samples = tuple(sample.to_dataset_sample() for sample in create_demo_alpaca_samples())
        dataset_samples += tuple(sample.to_dataset_sample() for sample in create_demo_sharegpt_samples())
        seeds = knowledge_seeds_from_dataset_samples(dataset_samples)

    clusters: tuple[GrapeCluster, ...] = ()
    growth_plan: GrowthPlan | None = None
    if seeds and (config.use_grape_clusters or config.use_growth_engine):
        review_decisions = tuple(KnowledgeReviewPipeline().review(seeds))
        clusters, assignments = GrapeClusterer(keyword_overlap_threshold=0.25).cluster(
            seeds,
            review_decisions,
        )
        if config.use_grape_clusters:
            records = memory_records_from_grape_clusters(clusters)
            memory_modules.append(
                InMemoryKeywordMemory(
                    records,
                    name="benchmark-grape-memory",
                    description="Deterministic memory from benchmark grape clusters.",
                )
            )
        if config.use_growth_engine:
            growth_plan = GrowthEngine().plan_growth(seeds, review_decisions, clusters, assignments)
            records = memory_records_from_growth_plan(growth_plan, clusters)
            memory_modules.append(
                InMemoryKeywordMemory(
                    records,
                    name="benchmark-growth-memory",
                    description="Deterministic memory from benchmark growth decisions.",
                )
            )
    elif seeds:
        memory_modules.append(
            InMemoryKeywordMemory(
                memory_records_from_seeds(seeds),
                name="benchmark-dataset-seed-memory",
                description="Deterministic memory from benchmark dataset seeds.",
            )
        )

    return tuple(memory_modules), growth_plan, clusters


def memory_records_from_seeds(seeds: Sequence[KnowledgeSeed]) -> tuple[MemoryRecord, ...]:
    """Create lightweight memory records from raw dataset seeds for benchmark context only."""
    return tuple(
        MemoryRecord(
            id=f"benchmark:{seed.id}",
            content=seed.content,
            domains=seed.domains,
            keywords=seed.keywords,
            source="benchmark_dataset_seed",
            metadata={"seed_id": seed.id, "seed_status": seed.status},
        )
        for seed in seeds
        if seed.content
    )


def selected_domain_labels(selected_modules: Sequence[str]) -> tuple[str, ...]:
    """Return stable high-level domain labels for selected demo modules."""
    domains: list[str] = []
    for module_name in selected_modules:
        label = MODULE_DOMAIN_LABELS.get(module_name, module_name)
        if label not in domains:
            domains.append(label)
    return tuple(domains)


def matched_values(expected: Sequence[str], observed: Sequence[str]) -> tuple[str, ...]:
    """Return expected values that appear in observed values, preserving expected order."""
    observed_set = {value.lower() for value in observed}
    return tuple(value for value in expected if value.lower() in observed_set)


def matched_keywords_in_text(expected_keywords: Sequence[str], text: str) -> tuple[str, ...]:
    """Return expected keywords found in normalized text."""
    terms = tokenize(text)
    return tuple(keyword for keyword in expected_keywords if keyword.lower() in terms)


def domain_match_score(expected_domains: Sequence[str], selected_domains: Sequence[str]) -> float:
    """Score expected domain coverage from 0.0 to 1.0."""
    return coverage_score(expected_domains, selected_domains)


def module_match_score(expected_modules: Sequence[str], selected_modules: Sequence[str]) -> float:
    """Score expected module coverage from 0.0 to 1.0."""
    return coverage_score(expected_modules, selected_modules)


def keyword_context_score(expected_keywords: Sequence[str], context_text: str) -> float:
    """Score whether expected keywords appear in built context or growth traces."""
    if not expected_keywords:
        return 1.0
    return round(len(matched_keywords_in_text(expected_keywords, context_text)) / len(expected_keywords), 3)


def routing_match_score(
    expected_domains: Sequence[str],
    selected_domains: Sequence[str],
    expected_modules: Sequence[str],
    selected_modules: Sequence[str],
) -> float:
    """Combine domain and module coverage into one routing score."""
    domain_score = domain_match_score(expected_domains, selected_domains)
    module_score = module_match_score(expected_modules, selected_modules)
    return round(domain_score * 0.45 + module_score * 0.55, 3)


def growth_decision_score(
    expected_domains: Sequence[str],
    expected_keywords: Sequence[str],
    growth_plan: GrowthPlan | None,
    clusters: Sequence[GrapeCluster] = (),
) -> float:
    """Score whether growth artifacts are relevant to the benchmark case."""
    if growth_plan is None or not growth_plan.decisions:
        return 0.0
    growth_text = " ".join(
        (
            growth_plan.to_text(),
            " ".join(cluster.domain for cluster in clusters),
            " ".join(keyword for cluster in clusters for keyword in cluster.keywords),
        )
    )
    domain_score = coverage_score(expected_domains, tokenize(growth_text))
    keyword_score = keyword_context_score(expected_keywords, growth_text)
    return round(domain_score * 0.4 + keyword_score * 0.6, 3)


def overall_benchmark_score(routing_score: float, context_score: float, growth_score: float) -> float:
    """Combine routing, context, and growth scores without LLM judging."""
    return round(
        clamp_score(routing_score) * 0.5
        + clamp_score(context_score) * 0.35
        + clamp_score(growth_score) * 0.15,
        3,
    )


def coverage_score(expected: Sequence[str], observed: Sequence[str] | set[str]) -> float:
    """Return deterministic coverage of expected labels in observed labels or tokens."""
    if not expected:
        return 1.0
    observed_set = {value.lower() for value in observed}
    matches = sum(1 for value in expected if value.lower() in observed_set)
    return round(matches / len(expected), 3)


def benchmark_context_text(
    case: BenchmarkCase,
    context_items: Sequence[ContextItem],
    growth_plan: GrowthPlan | None,
    clusters: Sequence[GrapeCluster],
) -> str:
    """Build one searchable text block for deterministic context scoring."""
    pieces = [case.task]
    pieces.extend(item.content for item in context_items)
    pieces.extend(str(value) for item in context_items for value in item.metadata.values())
    if growth_plan is not None:
        pieces.append(growth_plan.to_text())
    for cluster in clusters:
        pieces.extend((cluster.domain, cluster.name, " ".join(cluster.keywords)))
    return " ".join(pieces)


def average_score(values: Sequence[float] | object) -> float:
    """Average score values from any finite iterable."""
    materialized = tuple(values)
    if not materialized:
        return 0.0
    return round(sum(materialized) / len(materialized), 3)


def clamp_score(value: float) -> float:
    """Clamp score-like values to the 0.0..1.0 range."""
    return round(max(0.0, min(float(value), 1.0)), 3)


def summarize_result(result: BenchmarkResult) -> str:
    """Create a compact deterministic result summary."""
    return (
        f"matched {len(result.matched_expected_modules)} modules, "
        f"{len(result.matched_expected_domains)} domains, "
        f"and {len(result.matched_keywords)} context keywords"
    )


def summarize_report(config_name: str, results: Sequence[BenchmarkResult]) -> str:
    """Create a compact report summary."""
    if not results:
        return f"{config_name} ran no benchmark cases."
    return f"{config_name} ran {len(results)} deterministic benchmark cases."


def create_demo_benchmark_cases() -> tuple[BenchmarkCase, ...]:
    """Create small deterministic benchmark cases for current Grona demos."""
    return (
        BenchmarkCase(
            "auto-overheating",
            "Diagnose engine overheating in traffic and explain coolant inspection steps.",
            expected_domains=("automotive",),
            expected_modules=("automotive-diagnostics",),
            expected_keywords=("engine", "overheating", "coolant", "radiator"),
            workspace="automotive",
        ),
        BenchmarkCase(
            "security-code-review",
            "Review Python authentication code for security bugs and suspicious logs.",
            expected_domains=("code", "cybersecurity"),
            expected_modules=("code-assistant", "cybersecurity-scanner"),
            expected_keywords=("python", "security", "authentication", "logs"),
            workspace="cybersecurity",
        ),
        BenchmarkCase(
            "media-video-workflow",
            "Plan a video workflow with codec, color, audio, render, and metadata checks.",
            expected_domains=("media",),
            expected_modules=("media-video-tool",),
            expected_keywords=("video", "codec", "color", "audio", "render"),
            workspace="media",
        ),
        BenchmarkCase(
            "document-retrieval",
            "Find document indexing notes about chunks, citations, extraction, and summaries.",
            expected_domains=("document",),
            expected_modules=("document-search",),
            expected_keywords=("document", "indexing", "chunks", "citations"),
            workspace="documents",
        ),
        BenchmarkCase(
            "general-instruction-following",
            "Analyze an ambiguous plan and explain a small step-by-step approach.",
            expected_domains=("general",),
            expected_modules=("general-reasoning",),
            expected_keywords=("analyze", "plan", "explain", "steps"),
            workspace="default",
        ),
    )


def create_demo_benchmark_configs() -> tuple[BenchmarkRunConfig, ...]:
    """Create deterministic benchmark configs for baseline and enhanced comparisons."""
    return (
        BenchmarkRunConfig("baseline-routing"),
        BenchmarkRunConfig(
            "orchestrated-demo-memory",
            use_memory=True,
            use_demo_memory=True,
            use_orchestrator=True,
        ),
        BenchmarkRunConfig(
            "dataset-growth-demo",
            use_memory=True,
            use_demo_memory=True,
            use_dataset_seeds=True,
            use_grape_clusters=True,
            use_growth_engine=True,
            use_orchestrator=True,
        ),
    )
