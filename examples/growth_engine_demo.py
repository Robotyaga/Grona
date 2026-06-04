"""Demonstrate deterministic GrowthEngine planning."""

from collections import Counter

from grona import (
    GrapeClusterer,
    GrowthEngine,
    KnowledgeReviewPipeline,
    create_growth_engine_demo_seeds,
    memory_records_from_growth_plan,
)


def main() -> None:
    """Run the GrowthEngine demo pipeline."""
    seeds = create_growth_engine_demo_seeds()
    review_decisions = tuple(KnowledgeReviewPipeline().review(seeds))
    clusters, assignments = GrapeClusterer(keyword_overlap_threshold=0.3).cluster(
        seeds,
        review_decisions,
    )
    plan = GrowthEngine().plan_growth(seeds, review_decisions, clusters, assignments)
    records = memory_records_from_growth_plan(plan, clusters)

    print("GrowthEngine MVP demo")
    print(
        "Execution: deterministic recommendations only; "
        "no LLM, embeddings, web, APIs, or training."
    )
    print()
    print(f"Raw demo seeds: {len(seeds)}")
    print(f"Review decisions: {len(review_decisions)}")
    print(f"Candidate clusters: {len(clusters)}")
    print(f"Assignments: {len(assignments)}")
    print(f"Growth decisions: {len(plan.decisions)}")
    print(f"Memory records prepared from plan: {len(records)}")
    print()

    print("Review decision counts:")
    for decision, count in sorted(Counter(item.decision for item in review_decisions).items()):
        print(f"- {decision}: {count}")

    print("\nGrowth action counts:")
    for action, count in sorted(Counter(item.action for item in plan.decisions).items()):
        print(f"- {action}: {count}")

    print("\nClusters:")
    for cluster in clusters:
        print(
            f"- {cluster.id}: domain={cluster.domain}, "
            f"seeds={len(cluster.seed_ids)}, confidence={cluster.confidence:.2f}"
        )

    print("\nGrowth plan:")
    print(plan.to_text())

    print("\nPrepared memory records:")
    if not records:
        print("- none")
    for record in records:
        print(f"- {record.id}: {record.content}")


if __name__ == "__main__":
    main()
