"""Deterministic GrowthEngine recommendations for reviewed Growth Lab structures."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .feedback import Metadata
from .growth import KnowledgeSeed, KnowledgeSource
from .growth_clusters import (
    GrapeAssignment,
    GrapeCluster,
    GrapeClusterer,
    memory_records_from_grape_clusters,
)
from .growth_review import KnowledgeReviewPipeline, SeedReviewDecision
from .memory import MemoryRecord

GROWTH_TARGET_TYPES = ("seed", "node", "cluster", "memory", "expert_proposal")
GROWTH_ACTIONS = (
    "promote_seed",
    "merge_duplicate",
    "quarantine_seed",
    "reject_seed",
    "create_candidate_cluster",
    "strengthen_cluster",
    "mark_cluster_needs_review",
    "create_memory_record",
    "suggest_expert_candidate",
    "no_action",
)
SEED_DECISION_ACTIONS = {
    "reject_broken": "reject_seed",
    "merge_duplicate": "merge_duplicate",
    "quarantine_conflict": "quarantine_seed",
    "quarantine_weak": "quarantine_seed",
}


@dataclass(frozen=True)
class GrowthDecision:
    """One explainable recommended growth action."""

    id: str
    target_type: str
    target_id: str
    action: str
    confidence: float
    reasons: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        id: str,
        target_type: str,
        target_id: str,
        action: str,
        confidence: float,
        reasons: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "target_type", target_type)
        object.__setattr__(self, "target_id", target_id)
        object.__setattr__(self, "action", action)
        object.__setattr__(self, "confidence", round(confidence, 3))
        object.__setattr__(self, "reasons", tuple(reasons))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not id:
            raise ValueError("growth decision id cannot be empty")
        if target_type not in GROWTH_TARGET_TYPES:
            raise ValueError(f"unsupported growth target_type: {target_type}")
        if not target_id:
            raise ValueError("growth decision target_id cannot be empty")
        if action not in GROWTH_ACTIONS:
            raise ValueError(f"unsupported growth action: {action}")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("growth decision confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class GrowthPlan:
    """A deterministic set of recommended growth decisions."""

    decisions: tuple[GrowthDecision, ...] = ()
    summary: str = "No growth decisions."
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        decisions: Sequence[GrowthDecision] = (),
        summary: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        decision_tuple = tuple(decisions)
        object.__setattr__(self, "decisions", decision_tuple)
        object.__setattr__(self, "summary", summary or summarize_growth_decisions(decision_tuple))
        object.__setattr__(self, "metadata", dict(metadata or {}))

    def to_text(self) -> str:
        """Format the plan for humans."""
        lines = ["GrowthEngine plan", self.summary, "", "Decisions:"]
        if not self.decisions:
            lines.append("- none")
            return "\n".join(lines)
        for decision in self.decisions:
            lines.append(
                f"- {decision.id}: {decision.action} "
                f"{decision.target_type}:{decision.target_id} "
                f"(confidence={decision.confidence:.2f})"
            )
            lines.extend(f"  reason: {reason}" for reason in decision.reasons)
        return "\n".join(lines)


@dataclass(frozen=True)
class GrowthEngineConfig:
    """Conservative deterministic thresholds for GrowthEngine recommendations."""

    min_seed_confidence_for_promotion: float = 0.6
    min_cluster_confidence_for_memory: float = 0.65
    min_seeds_for_expert_candidate: int = 3
    quarantine_conflicts: bool = True
    promote_weak_seeds: bool = False
    max_decisions: int | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_seed_confidence_for_promotion <= 1.0:
            raise ValueError("min_seed_confidence_for_promotion must be between 0.0 and 1.0")
        if not 0.0 <= self.min_cluster_confidence_for_memory <= 1.0:
            raise ValueError("min_cluster_confidence_for_memory must be between 0.0 and 1.0")
        if self.min_seeds_for_expert_candidate < 1:
            raise ValueError("min_seeds_for_expert_candidate must be at least 1")
        if self.max_decisions is not None and self.max_decisions < 1:
            raise ValueError("max_decisions must be positive when provided")


class GrowthEngine:
    """Recommend the next explainable Growth Lab actions without mutating inputs."""

    def __init__(self, config: GrowthEngineConfig | None = None) -> None:
        self.config = config or GrowthEngineConfig()

    def plan_growth(
        self,
        seeds: Sequence[KnowledgeSeed],
        review_decisions: Sequence[SeedReviewDecision],
        clusters: Sequence[GrapeCluster],
        assignments: Sequence[GrapeAssignment],
    ) -> GrowthPlan:
        """Create deterministic growth recommendations from reviewed seeds and clusters."""
        seed_map = {seed.id: seed for seed in seeds}
        assignment_map = {assignment.seed_id: assignment for assignment in assignments}
        decisions: list[GrowthDecision] = []

        for index, review in enumerate(review_decisions, start=1):
            decision = self._decision_from_review(
                index,
                review,
                seed_map.get(review.seed_id),
                assignment_map.get(review.seed_id),
            )
            if decision is not None:
                decisions.append(decision)

        seed_decision_count = len(decisions)
        for index, cluster in enumerate(clusters, start=1):
            decisions.extend(self._decisions_from_cluster(index, cluster))

        limited = self._apply_limit(decisions)
        return GrowthPlan(
            limited,
            metadata={
                "seed_count": len(seeds),
                "review_decision_count": len(review_decisions),
                "cluster_count": len(clusters),
                "assignment_count": len(assignments),
                "seed_growth_decision_count": seed_decision_count,
                "decision_count": len(limited),
                "max_decisions_applied": self.config.max_decisions is not None,
            },
        )

    def _decision_from_review(
        self,
        index: int,
        review: SeedReviewDecision,
        seed: KnowledgeSeed | None,
        assignment: GrapeAssignment | None,
    ) -> GrowthDecision | None:
        seed_confidence = seed.confidence if seed is not None else 0.0
        metadata = seed_growth_metadata(review, assignment)
        if review.decision in SEED_DECISION_ACTIONS:
            return GrowthDecision(
                id=f"growth:seed:{index:04d}",
                target_type="seed",
                target_id=review.seed_id,
                action=SEED_DECISION_ACTIONS[review.decision],
                confidence=confidence_from_review(review, seed_confidence),
                reasons=review.reasons or (f"review decision is {review.decision}",),
                metadata=metadata,
            )

        if review.decision == "promote_candidate":
            if seed_confidence >= self.config.min_seed_confidence_for_promotion:
                return GrowthDecision(
                    id=f"growth:seed:{index:04d}",
                    target_type="seed",
                    target_id=review.seed_id,
                    action="promote_seed",
                    confidence=max(seed_confidence, confidence_from_review(review, seed_confidence)),
                    reasons=(
                        "review decision promotes seed candidate",
                        "seed confidence meets promotion threshold",
                    ),
                    metadata=metadata,
                )
            action = "promote_seed" if self.config.promote_weak_seeds else "quarantine_seed"
            reason = (
                "weak seed promotion is explicitly enabled"
                if self.config.promote_weak_seeds
                else "seed confidence is below promotion threshold"
            )
            return GrowthDecision(
                id=f"growth:seed:{index:04d}",
                target_type="seed",
                target_id=review.seed_id,
                action=action,
                confidence=max(seed_confidence, 0.5),
                reasons=("review decision promotes seed candidate", reason),
                metadata=metadata,
            )

        if review.decision == "needs_review":
            return GrowthDecision(
                id=f"growth:seed:{index:04d}",
                target_type="seed",
                target_id=review.seed_id,
                action="quarantine_seed" if self.config.quarantine_conflicts else "no_action",
                confidence=confidence_from_review(review, seed_confidence),
                reasons=review.reasons or ("seed needs human review before growth",),
                metadata=metadata,
            )
        return None

    def _decisions_from_cluster(
        self,
        index: int,
        cluster: GrapeCluster,
    ) -> list[GrowthDecision]:
        metadata = cluster_growth_metadata(cluster)
        if cluster_needs_review(cluster, self.config):
            return [
                GrowthDecision(
                    id=f"growth:cluster:{index:04d}:review",
                    target_type="cluster",
                    target_id=cluster.id,
                    action="mark_cluster_needs_review",
                    confidence=max(cluster.confidence, 0.5),
                    reasons=cluster_review_reasons(cluster, self.config),
                    metadata=metadata,
                )
            ]

        decisions: list[GrowthDecision] = []
        if cluster.status == "candidate":
            decisions.append(
                GrowthDecision(
                    id=f"growth:cluster:{index:04d}:candidate",
                    target_type="cluster",
                    target_id=cluster.id,
                    action="create_candidate_cluster",
                    confidence=cluster.confidence,
                    reasons=("candidate cluster is ready for explicit review",),
                    metadata=metadata,
                )
            )
        if len(cluster.seed_ids) >= 2:
            decisions.append(
                GrowthDecision(
                    id=f"growth:cluster:{index:04d}:strengthen",
                    target_type="cluster",
                    target_id=cluster.id,
                    action="strengthen_cluster",
                    confidence=cluster.confidence,
                    reasons=(
                        "cluster has multiple reviewed seeds",
                        "cluster confidence meets memory threshold",
                    ),
                    metadata=metadata,
                )
            )
        decisions.append(
            GrowthDecision(
                id=f"growth:cluster:{index:04d}:memory",
                target_type="memory",
                target_id=cluster.id,
                action="create_memory_record",
                confidence=cluster.confidence,
                reasons=("cluster is strong enough to prepare a memory bridge",),
                metadata=metadata,
            )
        )
        if should_suggest_expert(cluster, self.config):
            decisions.append(
                GrowthDecision(
                    id=f"growth:cluster:{index:04d}:expert",
                    target_type="expert_proposal",
                    target_id=cluster.id,
                    action="suggest_expert_candidate",
                    confidence=cluster.confidence,
                    reasons=(
                        "cluster has enough reviewed seeds for an expert proposal",
                        "cluster domain consistency is strong",
                    ),
                    metadata={**metadata, "domain_consistency": domain_consistency(cluster)},
                )
            )
        return decisions

    def _apply_limit(self, decisions: Sequence[GrowthDecision]) -> tuple[GrowthDecision, ...]:
        decision_tuple = tuple(decisions)
        if self.config.max_decisions is None:
            return decision_tuple
        return decision_tuple[: self.config.max_decisions]


def seed_growth_metadata(
    review: SeedReviewDecision,
    assignment: GrapeAssignment | None,
) -> Metadata:
    """Build metadata for seed-level growth recommendations."""
    metadata = {
        "review_decision": review.decision,
        "recommended_status": review.recommended_status,
        "duplicate_of": review.duplicate_of,
        "conflicts_with": list(review.conflicts_with),
        **review.metadata,
    }
    if assignment is not None:
        metadata.update(
            {
                "assigned": assignment.assigned,
                "cluster_id": assignment.cluster_id,
                "node_id": assignment.node_id,
            }
        )
    return metadata


def cluster_growth_metadata(cluster: GrapeCluster) -> Metadata:
    """Build metadata for cluster-level growth recommendations."""
    return {
        "domain": cluster.domain,
        "cluster_status": cluster.status,
        "seed_ids": list(cluster.seed_ids),
        "node_ids": [node.id for node in cluster.nodes],
        "keyword_count": len(cluster.keywords),
    }


def confidence_from_review(review: SeedReviewDecision, seed_confidence: float) -> float:
    """Return a deterministic confidence for review-driven actions."""
    validation_score = review.metadata.get("validation_score")
    if isinstance(validation_score, (int, float)):
        return round(max(seed_confidence, float(validation_score)), 3)
    duplicate_score = review.metadata.get("duplicate_score")
    if isinstance(duplicate_score, (int, float)) and duplicate_score > 0:
        return round(float(duplicate_score), 3)
    if review.conflicts_with:
        return max(seed_confidence, 0.7)
    return seed_confidence


def cluster_needs_review(cluster: GrapeCluster, config: GrowthEngineConfig) -> bool:
    """Return whether a cluster is too weak or conflicted for growth actions."""
    return bool(
        cluster.confidence < config.min_cluster_confidence_for_memory
        or cluster.metadata.get("conflicts_with")
        or cluster.status in {"needs_review", "quarantined"}
    )


def cluster_review_reasons(cluster: GrapeCluster, config: GrowthEngineConfig) -> tuple[str, ...]:
    """Return explicit reasons for a cluster review recommendation."""
    reasons = ["cluster needs review before memory or expert growth"]
    if cluster.confidence < config.min_cluster_confidence_for_memory:
        reasons.append("cluster confidence is below memory threshold")
    if cluster.metadata.get("conflicts_with"):
        reasons.append("cluster metadata includes potential conflicts")
    if cluster.status in {"needs_review", "quarantined"}:
        reasons.append(f"cluster status is {cluster.status}")
    return tuple(reasons)


def should_suggest_expert(cluster: GrapeCluster, config: GrowthEngineConfig) -> bool:
    """Return whether a cluster is strong enough for a future expert proposal."""
    return bool(
        len(cluster.seed_ids) >= config.min_seeds_for_expert_candidate
        and cluster.confidence >= config.min_cluster_confidence_for_memory
        and domain_consistency(cluster) >= 0.8
    )


def domain_consistency(cluster: GrapeCluster) -> float:
    """Estimate whether cluster nodes consistently belong to one domain."""
    if not cluster.nodes:
        return 0.0
    matching = sum(1 for node in cluster.nodes if node.domain == cluster.domain)
    return round(matching / len(cluster.nodes), 3)


def summarize_growth_decisions(decisions: Sequence[GrowthDecision]) -> str:
    """Summarize growth decisions by action."""
    if not decisions:
        return "No growth decisions."
    counts = Counter(decision.action for decision in decisions)
    pieces = [f"{action}={count}" for action, count in sorted(counts.items())]
    return f"{len(decisions)} growth decisions: " + ", ".join(pieces)


def memory_records_from_growth_plan(
    plan: GrowthPlan,
    clusters: Sequence[GrapeCluster],
) -> tuple[MemoryRecord, ...]:
    """Prepare memory records only for clusters selected by a growth plan."""
    selected_cluster_ids = {
        decision.target_id
        for decision in plan.decisions
        if decision.action == "create_memory_record" and decision.target_type == "memory"
    }
    selected_clusters = [cluster for cluster in clusters if cluster.id in selected_cluster_ids]
    return memory_records_from_grape_clusters(selected_clusters)


def create_demo_growth_plan() -> GrowthPlan:
    """Create a deterministic demo GrowthPlan from the current Growth Lab pipeline."""
    seeds = create_growth_engine_demo_seeds()
    review_decisions = tuple(KnowledgeReviewPipeline().review(seeds))
    clusters, assignments = GrapeClusterer(keyword_overlap_threshold=0.3).cluster(
        seeds,
        review_decisions,
    )
    return GrowthEngine().plan_growth(seeds, review_decisions, clusters, assignments)


def create_growth_engine_demo_seeds() -> tuple[KnowledgeSeed, ...]:
    """Create deterministic seeds that exercise GrowthEngine recommendations."""
    source = KnowledgeSource("source:growth-engine", "user_note", "GrowthEngine demo", 0.9)
    donor = KnowledgeSource("source:growth-engine-donor", "donor_model", "Weak donor", 0.35)
    unknown = KnowledgeSource("source:growth-engine-unknown", "unknown", "Unknown", 0.2)
    return (
        KnowledgeSeed(
            "seed:growth-auto-coolant",
            "Engine overheating triage supports coolant, radiator flow, and fan checks.",
            source,
            domains=("automotive",),
            keywords=("engine", "overheating", "coolant", "radiator"),
            confidence=0.9,
        ),
        KnowledgeSeed(
            "seed:growth-auto-thermostat",
            "Cooling diagnosis supports thermostat checks, coolant flow, and leak inspection.",
            source,
            domains=("automotive",),
            keywords=("coolant", "thermostat", "radiator", "leaks"),
            confidence=0.86,
        ),
        KnowledgeSeed(
            "seed:growth-auto-fan",
            "Engine cooling review supports fan activation, coolant checks, radiator flow, and leaks.",
            source,
            domains=("automotive",),
            keywords=("engine", "coolant", "radiator", "fan"),
            confidence=0.84,
        ),
        KnowledgeSeed(
            "seed:growth-auto-duplicate",
            "Engine overheating triage supports coolant, radiator flow, and fan checks.",
            source,
            domains=("automotive",),
            keywords=("engine", "overheating", "coolant", "radiator"),
            confidence=0.88,
        ),
        KnowledgeSeed(
            "seed:growth-security-positive",
            "Security review supports checking authentication, permissions, secrets, and logs.",
            source,
            domains=("cybersecurity",),
            keywords=("security", "authentication", "secrets", "logs"),
            confidence=0.82,
        ),
        KnowledgeSeed(
            "seed:growth-security-conflict",
            "Security review does not support checking authentication, permissions, secrets, or logs.",
            source,
            domains=("cybersecurity",),
            keywords=("security", "authentication", "secrets", "logs"),
            confidence=0.8,
        ),
        KnowledgeSeed(
            "seed:growth-weak-donor",
            "Unverified donor note says routing behavior might change but evidence is incomplete.",
            donor,
            domains=("general",),
            keywords=("routing", "evidence"),
            confidence=0.32,
        ),
        KnowledgeSeed(
            "seed:growth-broken-empty",
            "",
            unknown,
            domains=("general",),
            keywords=("empty",),
            confidence=0.2,
        ),
    )
