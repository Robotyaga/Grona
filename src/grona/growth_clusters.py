"""Deterministic GrapeNode and GrapeCluster structures for Growth Lab."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .feedback import Metadata
from .growth import KnowledgeSeed, KnowledgeSource
from .growth_review import KnowledgeReviewPipeline, SeedReviewDecision, normalize_keyword_values
from .memory import MemoryRecord

GRAPE_NODE_STATUSES = ("candidate", "active", "weak", "quarantined", "retired")
GRAPE_CLUSTER_STATUSES = ("candidate", "active", "needs_review", "quarantined", "retired")


@dataclass(frozen=True)
class GrapeNode:
    """Small organized knowledge unit inside one domain."""

    id: str
    name: str
    domain: str
    keywords: tuple[str, ...] = ()
    seed_ids: tuple[str, ...] = ()
    confidence: float = 0.5
    status: str = "candidate"
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        id: str,
        name: str,
        domain: str,
        keywords: Sequence[str] = (),
        seed_ids: Sequence[str] = (),
        confidence: float = 0.5,
        status: str = "candidate",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "domain", domain)
        object.__setattr__(self, "keywords", tuple(keywords))
        object.__setattr__(self, "seed_ids", tuple(seed_ids))
        object.__setattr__(self, "confidence", round(confidence, 3))
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not id:
            raise ValueError("grape node id cannot be empty")
        if not name:
            raise ValueError("grape node name cannot be empty")
        if not domain:
            raise ValueError("grape node domain cannot be empty")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("grape node confidence must be between 0.0 and 1.0")
        if status not in GRAPE_NODE_STATUSES:
            raise ValueError(f"unsupported grape node status: {status}")


@dataclass(frozen=True)
class GrapeCluster:
    """Group of related GrapeNodes within one domain."""

    id: str
    name: str
    domain: str
    nodes: tuple[GrapeNode, ...] = ()
    keywords: tuple[str, ...] = ()
    seed_ids: tuple[str, ...] = ()
    confidence: float = 0.5
    status: str = "candidate"
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        id: str,
        name: str,
        domain: str,
        nodes: Sequence[GrapeNode] = (),
        keywords: Sequence[str] = (),
        seed_ids: Sequence[str] = (),
        confidence: float = 0.5,
        status: str = "candidate",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "domain", domain)
        object.__setattr__(self, "nodes", tuple(nodes))
        object.__setattr__(self, "keywords", tuple(keywords))
        object.__setattr__(self, "seed_ids", tuple(seed_ids))
        object.__setattr__(self, "confidence", round(confidence, 3))
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not id:
            raise ValueError("grape cluster id cannot be empty")
        if not name:
            raise ValueError("grape cluster name cannot be empty")
        if not domain:
            raise ValueError("grape cluster domain cannot be empty")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("grape cluster confidence must be between 0.0 and 1.0")
        if status not in GRAPE_CLUSTER_STATUSES:
            raise ValueError(f"unsupported grape cluster status: {status}")


@dataclass(frozen=True)
class GrapeAssignment:
    """Trace showing how a seed was assigned to a cluster and node."""

    seed_id: str
    cluster_id: str | None
    node_id: str | None
    assigned: bool
    score: float
    reasons: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        seed_id: str,
        cluster_id: str | None,
        node_id: str | None,
        assigned: bool,
        score: float,
        reasons: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "seed_id", seed_id)
        object.__setattr__(self, "cluster_id", cluster_id)
        object.__setattr__(self, "node_id", node_id)
        object.__setattr__(self, "assigned", assigned)
        object.__setattr__(self, "score", round(score, 3))
        object.__setattr__(self, "reasons", tuple(reasons))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not seed_id:
            raise ValueError("grape assignment seed_id cannot be empty")
        if not 0.0 <= score <= 1.0:
            raise ValueError("grape assignment score must be between 0.0 and 1.0")


class GrapeClusterer:
    """Deterministic cluster builder for reviewed knowledge seeds."""

    def __init__(self, keyword_overlap_threshold: float = 0.35) -> None:
        if not 0.0 <= keyword_overlap_threshold <= 1.0:
            raise ValueError("keyword_overlap_threshold must be between 0.0 and 1.0")
        self.keyword_overlap_threshold = keyword_overlap_threshold

    def cluster(
        self,
        seeds: Sequence[KnowledgeSeed],
        decisions: Sequence[SeedReviewDecision],
    ) -> tuple[tuple[GrapeCluster, ...], tuple[GrapeAssignment, ...]]:
        """Create candidate clusters and assignments from reviewed seeds."""
        decision_map = {decision.seed_id: decision for decision in decisions}
        working: list[dict[str, object]] = []
        assignments: list[GrapeAssignment] = []

        for seed in seeds:
            decision = decision_map.get(seed.id)
            if decision is None:
                assignments.append(unassigned_seed(seed, "missing review decision"))
                continue
            if decision.decision != "promote_candidate":
                assignments.append(
                    unassigned_seed(seed, f"review decision is {decision.decision}")
                )
                continue
            cluster_data, score, reasons = self._find_or_create_cluster(seed, working)
            node = node_from_seed(seed, cluster_data)
            cluster_data["nodes"].append(node)
            cluster_data["seeds"].append(seed)
            cluster_data["keywords"].update(normalize_keyword_values(seed.keywords))
            assignments.append(
                GrapeAssignment(
                    seed.id,
                    cluster_id=str(cluster_data["id"]),
                    node_id=node.id,
                    assigned=True,
                    score=score,
                    reasons=reasons,
                    metadata={
                        "domain": primary_domain(seed),
                        "decision": decision.decision,
                        "source_id": seed.source.id,
                    },
                )
            )

        clusters = tuple(finalize_cluster(cluster_data) for cluster_data in working)
        return clusters, tuple(assignments)

    def _find_or_create_cluster(
        self,
        seed: KnowledgeSeed,
        working: list[dict[str, object]],
    ) -> tuple[dict[str, object], float, tuple[str, ...]]:
        domain = primary_domain(seed)
        seed_keywords = normalize_keyword_values(seed.keywords)
        best: tuple[float, dict[str, object]] | None = None
        for cluster_data in working:
            if cluster_data["domain"] != domain:
                continue
            score = keyword_overlap(seed_keywords, tuple(cluster_data["keywords"]))
            if best is None or score > best[0]:
                best = (score, cluster_data)
        if best is not None and best[0] >= self.keyword_overlap_threshold:
            return best[1], best[0], ("same primary domain", "keyword overlap with cluster")

        cluster_id = f"cluster:{slug(domain)}:{slug(seed_keywords[0] if seed_keywords else 'general')}"
        existing_ids = {str(cluster_data["id"]) for cluster_data in working}
        cluster_id = unique_id(cluster_id, existing_ids)
        cluster_data = {
            "id": cluster_id,
            "domain": domain,
            "keywords": set(seed_keywords),
            "nodes": [],
            "seeds": [],
        }
        working.append(cluster_data)
        return cluster_data, 1.0, ("created new cluster", "same primary domain")


def unassigned_seed(seed: KnowledgeSeed, reason: str) -> GrapeAssignment:
    """Create an explicit unassigned trace for ignored seeds."""
    return GrapeAssignment(
        seed.id,
        cluster_id=None,
        node_id=None,
        assigned=False,
        score=0.0,
        reasons=(reason,),
        metadata={"domain": primary_domain(seed), "source_id": seed.source.id},
    )


def node_from_seed(seed: KnowledgeSeed, cluster_data: Mapping[str, object]) -> GrapeNode:
    """Create a candidate node for one reviewed seed."""
    keywords = normalize_keyword_values(seed.keywords)
    node_index = len(cluster_data["nodes"]) + 1
    cluster_id = str(cluster_data["id"])
    node_id = f"node:{cluster_id.removeprefix('cluster:')}:{node_index:04d}"
    return GrapeNode(
        id=node_id,
        name=title_from_terms(keywords, fallback=seed.id),
        domain=primary_domain(seed),
        keywords=keywords,
        seed_ids=(seed.id,),
        confidence=seed_quality(seed),
        status="candidate",
        metadata={
            "source_id": seed.source.id,
            "source_reliability": seed.source.reliability,
            "seed_confidence": seed.confidence,
        },
    )


def finalize_cluster(cluster_data: Mapping[str, object]) -> GrapeCluster:
    """Convert mutable working cluster data into a frozen GrapeCluster."""
    nodes = tuple(cluster_data["nodes"])
    seeds = tuple(cluster_data["seeds"])
    keywords = aggregate_keywords(seeds)
    seed_ids = tuple(seed.id for seed in seeds)
    confidence = cluster_confidence(seeds)
    domain = str(cluster_data["domain"])
    return GrapeCluster(
        id=str(cluster_data["id"]),
        name=cluster_name(domain, keywords),
        domain=domain,
        nodes=nodes,
        keywords=keywords,
        seed_ids=seed_ids,
        confidence=confidence,
        status="candidate",
        metadata={
            "seed_count": len(seeds),
            "node_count": len(nodes),
            "source_ids": sorted({seed.source.id for seed in seeds}),
        },
    )


def cluster_confidence(seeds: Sequence[KnowledgeSeed]) -> float:
    """Calculate deterministic cluster confidence from seeds and sources."""
    if not seeds:
        return 0.0
    quality = sum(seed_quality(seed) for seed in seeds) / len(seeds)
    multi_seed_boost = min(max(len(seeds) - 1, 0) * 0.05, 0.15)
    small_cluster_penalty = 0.05 if len(seeds) == 1 else 0.0
    weak_penalty = sum(1 for seed in seeds if seed.confidence < 0.6) * 0.03
    return round(clamp(quality + multi_seed_boost - small_cluster_penalty - weak_penalty), 3)


def seed_quality(seed: KnowledgeSeed) -> float:
    """Return deterministic quality from seed confidence and source reliability."""
    return round(clamp(seed.confidence * 0.55 + seed.source.reliability * 0.45), 3)


def memory_records_from_grape_clusters(
    clusters: Sequence[GrapeCluster],
    include_statuses: Sequence[str] = ("candidate", "active"),
) -> tuple[MemoryRecord, ...]:
    """Convert candidate or active clusters into MemoryRecord bridge objects."""
    allowed = set(include_statuses)
    records: list[MemoryRecord] = []
    for cluster in clusters:
        if cluster.status not in allowed:
            continue
        content = (
            f"{cluster.name}: {len(cluster.nodes)} grape nodes from "
            f"{len(cluster.seed_ids)} reviewed knowledge seeds."
        )
        records.append(
            MemoryRecord(
                id=f"memory:{cluster.id}",
                content=content,
                domains=(cluster.domain,),
                keywords=cluster.keywords,
                source="grape_cluster",
                metadata={
                    "cluster_id": cluster.id,
                    "cluster_status": cluster.status,
                    "cluster_confidence": cluster.confidence,
                    "seed_ids": list(cluster.seed_ids),
                    "node_ids": [node.id for node in cluster.nodes],
                },
            )
        )
    return tuple(records)


def create_demo_grape_knowledge_seeds() -> tuple[KnowledgeSeed, ...]:
    """Create deterministic seeds for grape clustering demos."""
    source = KnowledgeSource("source:grape-demo", "user_note", "Grape demo notes", 0.88)
    return (
        KnowledgeSeed(
            "seed:grape-auto-coolant",
            "Engine overheating triage supports checking coolant, radiator flow, and fan activation.",
            source,
            domains=("automotive",),
            keywords=("engine", "overheating", "coolant", "radiator"),
            confidence=0.86,
        ),
        KnowledgeSeed(
            "seed:grape-auto-thermostat",
            "Cooling diagnosis supports thermostat checks, coolant circulation, and leak inspection.",
            source,
            domains=("automotive",),
            keywords=("coolant", "thermostat", "radiator", "leaks"),
            confidence=0.82,
        ),
        KnowledgeSeed(
            "seed:grape-security-inputs",
            "Security review supports input validation, authentication boundaries, and secrets checks.",
            source,
            domains=("cybersecurity",),
            keywords=("security", "validation", "authentication", "secrets"),
            confidence=0.85,
        ),
        KnowledgeSeed(
            "seed:grape-code-quality",
            "Code quality review supports tests, lint output, imports, and public API boundaries.",
            source,
            domains=("code",),
            keywords=("code", "tests", "lint", "api"),
            confidence=0.84,
        ),
        KnowledgeSeed(
            "seed:grape-media-workflow",
            "Media workflow review supports codec choice, color workflow, audio sync, and render checks.",
            source,
            domains=("media",),
            keywords=("media", "codec", "color", "render"),
            confidence=0.8,
        ),
        KnowledgeSeed(
            "seed:grape-document-retrieval",
            "Document retrieval review supports source metadata, chunk boundaries, citations, and summaries.",
            source,
            domains=("documents",),
            keywords=("documents", "retrieval", "chunks", "citations"),
            confidence=0.81,
        ),
        KnowledgeSeed(
            "seed:grape-weak-unassigned",
            "Possible weak donor note has incomplete evidence about routing behavior.",
            KnowledgeSource("source:grape-weak", "donor_model", "Weak donor", 0.35),
            domains=("general",),
            keywords=("routing", "evidence"),
            confidence=0.3,
        ),
    )


def create_demo_grape_clusters() -> tuple[GrapeCluster, ...]:
    """Create deterministic demo clusters through the review and cluster pipeline."""
    seeds = create_demo_grape_knowledge_seeds()
    decisions = KnowledgeReviewPipeline().review(seeds)
    clusters, _ = GrapeClusterer().cluster(seeds, decisions)
    return clusters


def create_demo_grape_nodes() -> tuple[GrapeNode, ...]:
    """Create deterministic demo nodes through the review and cluster pipeline."""
    return tuple(node for cluster in create_demo_grape_clusters() for node in cluster.nodes)


def aggregate_keywords(seeds: Sequence[KnowledgeSeed]) -> tuple[str, ...]:
    """Aggregate seed keywords by frequency and deterministic name."""
    counts: Counter[str] = Counter()
    for seed in seeds:
        counts.update(normalize_keyword_values(seed.keywords))
    return tuple(keyword for keyword, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def primary_domain(seed: KnowledgeSeed) -> str:
    """Return the deterministic primary domain for one seed."""
    domains = normalize_keyword_values(seed.domains)
    return domains[0] if domains else "general"


def keyword_overlap(left: Sequence[str], right: Sequence[str]) -> float:
    """Return keyword intersection over the smaller non-empty set."""
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / min(len(left_set), len(right_set))


def cluster_name(domain: str, keywords: Sequence[str]) -> str:
    """Create a human-readable deterministic cluster name."""
    if keywords:
        return f"{title_from_terms((domain, keywords[0]))} Cluster"
    return f"{title_from_terms((domain,))} Cluster"


def title_from_terms(terms: Sequence[str], fallback: str = "Grape") -> str:
    """Create a compact title from normalized terms."""
    visible = [term.replace("-", " ").replace("_", " ").title().replace(" ", "") for term in terms]
    return "".join(visible[:3]) or fallback


def slug(value: str) -> str:
    """Create a deterministic id slug."""
    cleaned = "".join(character if character.isalnum() else "-" for character in value.lower())
    return "-".join(part for part in cleaned.split("-") if part) or "general"


def unique_id(base: str, existing: set[str]) -> str:
    """Return an id that is unique within an existing id set."""
    if base not in existing:
        return base
    index = 2
    while f"{base}-{index}" in existing:
        index += 1
    return f"{base}-{index}"


def clamp(value: float) -> float:
    """Clamp confidence-like values to the 0.0..1.0 range."""
    return max(0.0, min(value, 1.0))
