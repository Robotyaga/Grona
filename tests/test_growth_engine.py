from collections import Counter

from grona import (
    GrapeAssignment,
    GrapeCluster,
    GrapeNode,
    GrowthDecision,
    GrowthEngine,
    GrowthEngineConfig,
    GrowthPlan,
    KnowledgeSeed,
    KnowledgeSource,
    SeedReviewDecision,
    create_growth_engine_demo_seeds,
    memory_records_from_growth_plan,
)
from grona.cli import main
from grona.growth_clusters import GrapeClusterer
from grona.growth_review import KnowledgeReviewPipeline


def make_seed(seed_id: str, confidence: float = 0.8) -> KnowledgeSeed:
    return KnowledgeSeed(
        seed_id,
        "A useful deterministic growth engine test seed with enough evidence.",
        KnowledgeSource("source:test", "user_note", "Test source", 0.9),
        domains=("code",),
        keywords=("code", "tests", "growth"),
        confidence=confidence,
    )


def make_review(
    seed_id: str,
    decision: str,
    confidence: float = 0.8,
    duplicate_of: str | None = None,
    conflicts_with: tuple[str, ...] = (),
) -> SeedReviewDecision:
    return SeedReviewDecision(
        seed_id,
        decision,
        reasons=(f"test review decision {decision}",),
        duplicate_of=duplicate_of,
        conflicts_with=conflicts_with,
        recommended_status="validated",
        metadata={"validation_score": confidence, "duplicate_score": confidence},
    )


def make_cluster(
    seed_count: int = 3,
    confidence: float = 0.86,
    status: str = "candidate",
    metadata: dict[str, object] | None = None,
) -> GrapeCluster:
    nodes = tuple(
        GrapeNode(
            f"node:code:{index:04d}",
            f"CodeNode{index}",
            "code",
            keywords=("code", "tests"),
            seed_ids=(f"seed:{index}",),
            confidence=confidence,
        )
        for index in range(1, seed_count + 1)
    )
    return GrapeCluster(
        "cluster:code:tests",
        "CodeTests Cluster",
        "code",
        nodes=nodes,
        keywords=("code", "tests", "growth"),
        seed_ids=tuple(f"seed:{index}" for index in range(1, seed_count + 1)),
        confidence=confidence,
        status=status,
        metadata=metadata or {"seed_count": seed_count},
    )


def action_counts(plan: GrowthPlan) -> Counter[str]:
    return Counter(decision.action for decision in plan.decisions)


def test_growth_decision_creation() -> None:
    decision = GrowthDecision(
        "growth:test",
        "seed",
        "seed:test",
        "promote_seed",
        0.81234,
        reasons=("clear reason",),
        metadata={"kind": "unit"},
    )

    assert decision.confidence == 0.812
    assert decision.reasons == ("clear reason",)
    assert decision.metadata == {"kind": "unit"}


def test_growth_plan_formatting() -> None:
    plan = GrowthPlan(
        [GrowthDecision("growth:test", "seed", "seed:test", "promote_seed", 0.8)],
    )

    text = plan.to_text()

    assert "GrowthEngine plan" in text
    assert "promote_seed seed:seed:test" in text
    assert "1 growth decisions" in plan.summary


def test_growth_engine_config_defaults() -> None:
    config = GrowthEngineConfig()

    assert config.min_seed_confidence_for_promotion == 0.6
    assert config.min_cluster_confidence_for_memory == 0.65
    assert config.min_seeds_for_expert_candidate == 3
    assert config.quarantine_conflicts is True
    assert config.promote_weak_seeds is False


def test_growth_engine_rejects_broken_seeds() -> None:
    seed = make_seed("seed:broken")
    review = make_review(seed.id, "reject_broken")

    plan = GrowthEngine().plan_growth([seed], [review], [], [])

    assert plan.decisions[0].action == "reject_seed"
    assert plan.decisions[0].target_id == seed.id


def test_growth_engine_merges_duplicates() -> None:
    seed = make_seed("seed:duplicate")
    review = make_review(seed.id, "merge_duplicate", duplicate_of="seed:canonical")

    plan = GrowthEngine().plan_growth([seed], [review], [], [])

    assert plan.decisions[0].action == "merge_duplicate"
    assert plan.decisions[0].metadata["duplicate_of"] == "seed:canonical"


def test_growth_engine_quarantines_conflicts() -> None:
    seed = make_seed("seed:conflict")
    review = make_review(seed.id, "quarantine_conflict", conflicts_with=("seed:other",))

    plan = GrowthEngine().plan_growth([seed], [review], [], [])

    assert plan.decisions[0].action == "quarantine_seed"
    assert plan.decisions[0].metadata["conflicts_with"] == ["seed:other"]


def test_growth_engine_promotes_clean_seed() -> None:
    seed = make_seed("seed:clean", confidence=0.78)
    review = make_review(seed.id, "promote_candidate", confidence=0.78)

    plan = GrowthEngine().plan_growth([seed], [review], [], [])

    assert plan.decisions[0].action == "promote_seed"
    assert "promotion threshold" in " ".join(plan.decisions[0].reasons)


def test_growth_engine_creates_memory_record_decision_for_strong_cluster() -> None:
    cluster = make_cluster(seed_count=2, confidence=0.82)

    plan = GrowthEngine().plan_growth([], [], [cluster], [])

    assert "create_memory_record" in action_counts(plan)
    assert "strengthen_cluster" in action_counts(plan)


def test_growth_engine_suggests_expert_candidate_for_strong_cluster() -> None:
    cluster = make_cluster(seed_count=3, confidence=0.88)

    plan = GrowthEngine().plan_growth([], [], [cluster], [])

    expert = next(decision for decision in plan.decisions if decision.action == "suggest_expert_candidate")
    assert expert.target_type == "expert_proposal"
    assert expert.metadata["domain_consistency"] == 1.0


def test_growth_engine_marks_weak_or_conflicted_cluster_as_needs_review() -> None:
    weak = make_cluster(seed_count=2, confidence=0.5)
    conflicted = make_cluster(
        seed_count=2,
        confidence=0.8,
        metadata={"conflicts_with": ["seed:other"]},
    )

    plan = GrowthEngine().plan_growth([], [], [weak, conflicted], [])

    assert action_counts(plan) == {"mark_cluster_needs_review": 2}


def test_growth_plan_is_deterministic() -> None:
    seeds = create_growth_engine_demo_seeds()
    reviews = tuple(KnowledgeReviewPipeline().review(seeds))
    clusters, assignments = GrapeClusterer(keyword_overlap_threshold=0.3).cluster(seeds, reviews)
    engine = GrowthEngine()

    first = engine.plan_growth(seeds, reviews, clusters, assignments)
    second = engine.plan_growth(seeds, reviews, clusters, assignments)

    assert first == second
    assert "suggest_expert_candidate" in action_counts(first)
    assert "merge_duplicate" in action_counts(first)
    assert "quarantine_seed" in action_counts(first)
    assert "reject_seed" in action_counts(first)


def test_memory_records_from_growth_plan() -> None:
    cluster = make_cluster(seed_count=3, confidence=0.88)
    plan = GrowthEngine().plan_growth([], [], [cluster], [])

    records = memory_records_from_growth_plan(plan, [cluster])

    assert len(records) == 1
    assert records[0].metadata["cluster_id"] == cluster.id


def test_cli_growth_engine_demo_behavior(capsys) -> None:
    assert main(["--growth-engine-demo"]) == 0

    output = capsys.readouterr().out
    assert "Growth Lab demo: GrowthEngine MVP" in output
    assert "Growth decisions:" in output
    assert "Decision counts by action:" in output
    assert "suggest_expert_candidate" in output
    assert "Prepared memory records:" in output
