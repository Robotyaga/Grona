"""Demonstrate deterministic Growth Lab grape cluster creation."""

from grona import (
    ContextBuilder,
    GrapeClusterer,
    InMemoryKeywordMemory,
    KnowledgeReviewPipeline,
    Router,
    create_default_registry,
    create_demo_grape_knowledge_seeds,
    memory_records_from_grape_clusters,
)


def main() -> None:
    """Run a small deterministic grape cluster and memory bridge demo."""
    seeds = create_demo_grape_knowledge_seeds()
    decisions = tuple(KnowledgeReviewPipeline().review(seeds))
    clusters, assignments = GrapeClusterer().cluster(seeds, decisions)
    records = memory_records_from_grape_clusters(clusters)

    print("GrapeCluster demo")
    print("Execution: deterministic only; no LLM, embeddings, web, APIs, or training.")
    print()
    print(f"Seeds: {len(seeds)}")
    print(f"Clusters: {len(clusters)}")
    print(f"Assignments: {len(assignments)}")
    print(f"Memory records: {len(records)}")
    print()

    for cluster in clusters:
        print(f"- {cluster.id}: {cluster.name} ({cluster.domain}, {cluster.confidence:.2f})")
        for node in cluster.nodes:
            print(f"  - {node.id}: {node.name} ({node.confidence:.2f})")

    memory = InMemoryKeywordMemory(
        records,
        name="grape-cluster-memory",
        description="Deterministic memory records made from grape clusters.",
    )
    task = "Diagnose engine overheating and coolant circulation issues"
    decision = Router(create_default_registry()).route(task)
    context_items = ContextBuilder(
        memory_modules=(memory,),
        include_stub_context=False,
    ).build(decision, task)

    print()
    print("Memory bridge context:")
    for item in context_items:
        print(f"- {item.source}: relevance={item.relevance:.2f}")
        print(f"  {item.content}")


if __name__ == "__main__":
    main()
