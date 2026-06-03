"""Demonstrate deterministic KnowledgeSeed review before future promotion."""

from collections import Counter

from grona import (
    KnowledgeConflictDetector,
    KnowledgeDeduplicator,
    KnowledgeReviewPipeline,
    KnowledgeValidator,
    create_demo_review_knowledge_seeds,
)


def main() -> None:
    seeds = create_demo_review_knowledge_seeds()
    validator = KnowledgeValidator()
    deduplicator = KnowledgeDeduplicator()
    conflict_detector = KnowledgeConflictDetector()
    pipeline = KnowledgeReviewPipeline(
        validator=validator,
        deduplicator=deduplicator,
        conflict_detector=conflict_detector,
    )

    validations = {result.seed_id: result for result in (validator.validate(seed) for seed in seeds)}
    duplicates = {result.seed_id: result for result in deduplicator.find_duplicates(seeds)}
    conflicts = {result.seed_id: result for result in conflict_detector.find_conflicts(seeds)}
    decisions = pipeline.review(seeds)
    counts = Counter(decision.decision for decision in decisions)

    print("Growth Lab KnowledgeSeed review demo")
    print("Deterministic review only; no LLM, embeddings, web, APIs, or training.")
    print()
    print(f"Total seeds: {len(seeds)}")
    for decision, count in sorted(counts.items()):
        print(f"{decision}: {count}")

    for decision in decisions:
        validation = validations[decision.seed_id]
        duplicate = duplicates[decision.seed_id]
        conflict = conflicts[decision.seed_id]
        print("=" * 80)
        print(f"Seed: {decision.seed_id}")
        print(f"Validation: {validation.status} (score {validation.score:.2f})")
        print(f"Duplicate: {duplicate.is_duplicate}; duplicate_of={duplicate.duplicate_of}")
        print(
            f"Potential conflict: {conflict.conflict_detected}; "
            f"severity={conflict.severity}; conflicts_with={conflict.conflicts_with}"
        )
        print(f"Decision: {decision.decision}")
        print(f"Recommended status: {decision.recommended_status}")
        if decision.reasons:
            print("Reasons:")
            for reason in decision.reasons:
                print(f"- {reason}")


if __name__ == "__main__":
    main()
