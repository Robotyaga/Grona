from collections import Counter

from grona import (
    GrapeAssignment,
    GrapeCluster,
    GrapeClusterer,
    GrapeNode,
    KnowledgeReviewPipeline,
    KnowledgeSeed,
    KnowledgeSource,
    create_demo_grape_clusters,
    create_demo_grape_knowledge_seeds,
    create_demo_grape_nodes,
    memory_records_from_grape_clusters,
)
from grona.cli import main
from grona.growth_review import SeedReviewDecision


def make_seed(
    seed_id: str,
    domain: str,
    keywords: tuple[str, ...],
    content: str | None = None,
    confidence: float = 0.85,
    reliability: float = 0.9,
) -> KnowledgeSeed:
    source = KnowledgeSource(
        f"source:{seed_id}",
        "user_note",
        f"Source {seed_id}",
        reliability,
    )
    if content is None:
        content = f"Useful {domain} note covering {', '.join(keywords)} with clear evidence."
    return KnowledgeSeed(
        id=seed_id,
        content=content,
        source=source,
        domains=(domain,),
        keywords=keywords,
        confidence=confidence,
    )


def promote_decisions(seeds: tuple[KnowledgeSeed, ...]) -> tuple[SeedReviewDecision, ...]:
    return tuple(
        SeedReviewDecision(
            seed.id,
            "promote_candidate",
            reasons=("test decision",),
            recommended_status="validated",
        )
        for seed in seeds
    )


def test_grape_node_creation() -> None:
    node = GrapeNode(
        id="node:test:0001",
        name="CoolingNode",
        domain="automotive",
        keywords=("coolant", "radiator"),
        seed_ids=("seed:auto",),
        confidence=0.81234,
        metadata={"source_id": "source:auto"},
    )

    assert node.id == "node:test:0001"
    assert node.confidence == 0.812
    assert node.status == "candidate"
    assert node.metadata["source_id"] == "source:auto"


def test_grape_cluster_creation() -> None:
    node = GrapeNode("node:test:0001", "CoolingNode", "automotive")
    cluster = GrapeCluster(
        id="cluster:automotive:coolant",
        name="AutomotiveCoolant Cluster",
        domain="automotive",
        nodes=(node,),
        keywords=("coolant",),
        seed_ids=("seed:auto",),
        confidence=0.9,
    )

    assert cluster.nodes == (node,)
    assert cluster.seed_ids == ("seed:auto",)
    assert cluster.status == "candidate"


def test_grape_assignment_creation() -> None:
    assignment = GrapeAssignment(
        seed_id="seed:auto",
        cluster_id="cluster:auto",
        node_id="node:auto:0001",
        assigned=True,
        score=0.7777,
        reasons=("same primary domain",),
    )

    assert assignment.assigned is True
    assert assignment.score == 0.778
    assert assignment.reasons == ("same primary domain",)


def test_clusterer_groups_seeds_by_domain_and_keyword_overlap() -> None:
    seeds = (
        make_seed("seed:auto-coolant", "automotive", ("coolant", "radiator", "engine")),
        make_seed(
            "seed:auto-thermostat",
            "automotive",
            ("coolant", "thermostat", "engine"),
        ),
        make_seed("seed:security", "cybersecurity", ("security", "validation", "secrets")),
    )
    decisions = promote_decisions(seeds)

    clusters, assignments = GrapeClusterer(keyword_overlap_threshold=0.3).cluster(
        seeds,
        decisions,
    )

    domains = Counter(cluster.domain for cluster in clusters)
    automotive = next(cluster for cluster in clusters if cluster.domain == "automotive")

    assert domains == {"automotive": 1, "cybersecurity": 1}
    assert len(automotive.nodes) == 2
    assert all(assignment.reasons for assignment in assignments)


def test_clusterer_ignores_non_promote_review_decisions() -> None:
    seeds = (
        make_seed("seed:strong", "code", ("tests", "lint", "api")),
        make_seed(
            "seed:weak",
            "general",
            ("routing", "evidence"),
            content="Incomplete weak note about routing behavior.",
            confidence=0.2,
            reliability=0.3,
        ),
    )
    decisions = KnowledgeReviewPipeline().review(seeds)

    clusters, assignments = GrapeClusterer().cluster(seeds, decisions)

    weak_assignment = next(
        assignment for assignment in assignments if assignment.seed_id == "seed:weak"
    )
    assert len(clusters) == 1
    assert weak_assignment.assigned is False
    assert weak_assignment.cluster_id is None
    assert "review decision is" in weak_assignment.reasons[0]


def test_cluster_confidence_is_deterministic() -> None:
    seeds = create_demo_grape_knowledge_seeds()
    decisions = KnowledgeReviewPipeline().review(seeds)
    clusterer = GrapeClusterer()

    first_clusters, first_assignments = clusterer.cluster(seeds, decisions)
    second_clusters, second_assignments = clusterer.cluster(seeds, decisions)

    assert first_clusters == second_clusters
    assert first_assignments == second_assignments


def test_memory_records_from_grape_clusters() -> None:
    clusters = create_demo_grape_clusters()

    records = memory_records_from_grape_clusters(clusters)

    assert len(records) == len(clusters)
    assert all(record.source == "grape_cluster" for record in records)
    assert all(record.metadata["cluster_id"] for record in records)


def test_demo_cluster_creation_is_deterministic() -> None:
    first_clusters = create_demo_grape_clusters()
    second_clusters = create_demo_grape_clusters()
    nodes = create_demo_grape_nodes()

    assert first_clusters == second_clusters
    assert len(first_clusters) == 5
    assert len(nodes) == 6
    assert {cluster.domain for cluster in first_clusters} == {
        "automotive",
        "code",
        "cybersecurity",
        "documents",
        "media",
    }


def test_cli_grape_demo_behavior(capsys) -> None:
    assert main(["--grape-demo"]) == 0

    output = capsys.readouterr().out
    assert "Growth Lab demo: GrapeCluster structures" in output
    assert "Clusters: 5" in output
    assert "Nodes: 6" in output
    assert "Memory records: 5" in output
    assert "seed:grape-weak-unassigned: assigned=False" in output
