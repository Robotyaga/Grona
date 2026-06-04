"""Run the deterministic Dataset Ingestion Foundation demo."""

from collections import Counter

from grona import (
    AlpacaFormatAdapter,
    GrapeClusterer,
    GrowthEngine,
    KnowledgeReviewPipeline,
    KnowledgeValidator,
    ShareGPTFormatAdapter,
    create_demo_dataset_sources,
    knowledge_seeds_from_dataset_samples,
)


def main() -> None:
    """Normalize tiny in-memory dataset records into Growth Lab seeds."""
    sources = create_demo_dataset_sources()
    alpaca_records = (
        {
            "instruction": "Explain how to review a Python function for missing tests.",
            "input": "A utility function changed without a focused regression test.",
            "output": "Check expected behavior, edge cases, imports, and add a small test.",
        },
        {"instruction": "This broken demo row has no output."},
    )
    sharegpt_records = (
        {
            "conversations": [
                {"from": "human", "value": "How should I inspect suspicious firewall logs?"},
                {
                    "from": "gpt",
                    "value": "Check source IPs, ports, auth failures, and timing patterns.",
                },
            ]
        },
    )

    instruction_samples = AlpacaFormatAdapter().parse(alpaca_records, sources["alpaca"])
    conversation_samples = ShareGPTFormatAdapter().parse(
        sharegpt_records,
        sources["sharegpt"],
    )
    dataset_samples = tuple(sample.to_dataset_sample() for sample in instruction_samples)
    dataset_samples += tuple(sample.to_dataset_sample() for sample in conversation_samples)
    seeds = knowledge_seeds_from_dataset_samples(dataset_samples)

    validator = KnowledgeValidator()
    validations = tuple(validator.validate(seed) for seed in seeds)
    review_decisions = tuple(KnowledgeReviewPipeline().review(seeds))
    clusters, assignments = GrapeClusterer(keyword_overlap_threshold=0.25).cluster(
        seeds,
        review_decisions,
    )
    plan = GrowthEngine().plan_growth(seeds, review_decisions, clusters, assignments)

    print("Dataset Ingestion Foundation demo")
    print("Execution: deterministic in-memory normalization only; no downloads or training.")
    print()
    print(f"Instruction samples: {len(instruction_samples)}")
    print(f"Conversation samples: {len(conversation_samples)}")
    print(f"Dataset samples: {len(dataset_samples)}")
    print(f"KnowledgeSeeds: {len(seeds)}")
    print(f"Clusters: {len(clusters)}")
    print(f"Growth decisions: {len(plan.decisions)}")
    print()
    print("Validation statuses:")
    for status, count in sorted(Counter(result.status for result in validations).items()):
        print(f"- {status}: {count}")
    print()
    print("Seeds:")
    for seed in seeds:
        print(
            f"- {seed.id}: type={seed.metadata['sample_type']}, "
            f"license={seed.metadata['dataset_license']}, "
            f"language={seed.metadata['dataset_language']}"
        )
    print()
    print(plan.to_text())


if __name__ == "__main__":
    main()
