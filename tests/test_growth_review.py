from collections import Counter

from grona import (
    ConflictCheckResult,
    DuplicateCheckResult,
    KnowledgeConflictDetector,
    KnowledgeDeduplicator,
    KnowledgeReviewPipeline,
    KnowledgeSeed,
    KnowledgeSource,
    NormalizedKnowledge,
    SeedReviewDecision,
    create_demo_review_knowledge_seeds,
)
from grona.cli import main


def seed(
    seed_id: str,
    content: str,
    domains=("code",),
    keywords=("python", "tests", "lint"),
    reliability: float = 0.9,
    confidence: float = 0.85,
) -> KnowledgeSeed:
    source = KnowledgeSource("source:test", "user_note", "Test source", reliability)
    return KnowledgeSeed(
        id=seed_id,
        content=content,
        source=source,
        domains=domains,
        keywords=keywords,
        confidence=confidence,
    )


def test_normalization_collapses_case_whitespace_and_punctuation() -> None:
    item = KnowledgeDeduplicator().normalize(
        seed(
            "seed:norm",
            "  Python, tests!!   and LINT checks.  ",
            keywords=("Python", "tests!", "tests"),
        )
    )

    assert isinstance(item, NormalizedKnowledge)
    assert item.normalized_content == "python tests and lint checks"
    assert item.normalized_keywords == ("python", "tests")


def test_exact_duplicate_detection() -> None:
    seeds = [
        seed("seed:a", "Python tests support lint checks and public API review."),
        seed("seed:b", "python tests support lint checks and public api review"),
    ]

    results = KnowledgeDeduplicator().find_duplicates(seeds)

    assert results[0].is_duplicate is False
    assert results[1].is_duplicate is True
    assert results[1].duplicate_of == "seed:a"
    assert "exact normalized content duplicate" in results[1].reasons


def test_keyword_overlap_duplicate_detection() -> None:
    seeds = [
        seed("seed:a", "Code review supports checking tests, lint, imports, and API boundaries."),
        seed("seed:b", "Review notes should inspect tests, lint, imports, and API boundaries."),
    ]

    results = KnowledgeDeduplicator().find_duplicates(seeds)

    assert results[1].is_duplicate is True
    assert results[1].duplicate_of == "seed:a"
    assert "high keyword overlap within the same domain" in results[1].reasons


def test_no_false_duplicate_for_different_domains() -> None:
    seeds = [
        seed("seed:code", "Code review supports tests and lint checks.", domains=("code",)),
        seed(
            "seed:auto",
            "Automotive review supports tests and lint checks for a diagnostic worksheet.",
            domains=("automotive",),
        ),
    ]

    results = KnowledgeDeduplicator().find_duplicates(seeds)

    assert all(result.is_duplicate is False for result in results)


def test_simple_conflict_detection_with_negation() -> None:
    seeds = [
        seed(
            "seed:allowed",
            "Workspace policy supports enabled demo tools for dry run review.",
            domains=("tools",),
            keywords=("workspace", "tools", "dry-run"),
        ),
        seed(
            "seed:blocked",
            "Workspace policy does not support enabled demo tools for dry run review.",
            domains=("tools",),
            keywords=("workspace", "tools", "dry-run"),
        ),
    ]

    results = KnowledgeConflictDetector().find_conflicts(seeds)

    assert results[0].conflict_detected is True
    assert results[0].conflicts_with == ("seed:blocked",)
    assert results[0].severity in {"medium", "high"}
    assert "potential conflict" in results[0].reasons[0]


def test_no_conflict_for_unrelated_seeds() -> None:
    seeds = [
        seed(
            "seed:code",
            "Code review supports checking tests, lint output, and imports.",
            domains=("code",),
            keywords=("tests", "lint", "imports"),
        ),
        seed(
            "seed:auto",
            "Engine overheating supports checking coolant and radiator flow.",
            domains=("automotive",),
            keywords=("engine", "coolant", "radiator"),
        ),
    ]

    results = KnowledgeConflictDetector().find_conflicts(seeds)

    assert all(result.conflict_detected is False for result in results)


def test_result_models_creation() -> None:
    duplicate = DuplicateCheckResult("seed:b", "seed:a", True, 1.0, ("duplicate",))
    conflict = ConflictCheckResult("seed:a", ("seed:b",), True, "medium", ("potential",))
    decision = SeedReviewDecision(
        "seed:a",
        "needs_review",
        reasons=("manual review",),
        conflicts_with=("seed:b",),
        recommended_status="quarantined",
    )

    assert duplicate.is_duplicate is True
    assert conflict.conflict_detected is True
    assert decision.decision == "needs_review"


def test_review_pipeline_rejects_broken_seed() -> None:
    broken = seed("seed:broken", "", domains=("general",), keywords=("empty",), confidence=0.2)

    decision = KnowledgeReviewPipeline().review([broken])[0]

    assert decision.decision == "reject_broken"
    assert decision.recommended_status == "rejected"


def test_review_pipeline_merges_duplicates() -> None:
    seeds = [
        seed("seed:a", "Python tests support lint checks and public API review."),
        seed("seed:b", "Python tests support lint checks and public API review."),
    ]

    decisions = KnowledgeReviewPipeline().review(seeds)

    assert decisions[0].decision == "promote_candidate"
    assert decisions[1].decision == "merge_duplicate"
    assert decisions[1].duplicate_of == "seed:a"


def test_review_pipeline_quarantines_conflicts() -> None:
    seeds = [
        seed(
            "seed:enabled",
            "Workspace demo tools are enabled and safe for dry run review.",
            domains=("tools",),
            keywords=("workspace", "tools", "dry-run"),
        ),
        seed(
            "seed:disabled",
            "Workspace demo tools are disabled and unsafe for dry run review.",
            domains=("tools",),
            keywords=("workspace", "tools", "policy"),
        ),
    ]

    decisions = KnowledgeReviewPipeline().review(seeds)
    by_id = {decision.seed_id: decision for decision in decisions}

    assert by_id["seed:enabled"].decision == "quarantine_conflict"
    assert by_id["seed:disabled"].decision == "quarantine_conflict"


def test_review_pipeline_marks_clean_seed_as_promote_candidate() -> None:
    clean = seed(
        "seed:clean",
        "Code review supports checking tests, lint output, imports, and public API boundaries.",
    )

    decision = KnowledgeReviewPipeline().review([clean])[0]

    assert decision.decision == "promote_candidate"
    assert decision.recommended_status == "validated"


def test_demo_review_seeds_produce_deterministic_decision_counts() -> None:
    decisions = KnowledgeReviewPipeline().review(create_demo_review_knowledge_seeds())
    counts = Counter(decision.decision for decision in decisions)

    assert counts["promote_candidate"] >= 1
    assert counts["merge_duplicate"] >= 2
    assert counts["quarantine_conflict"] >= 1
    assert counts["quarantine_weak"] >= 1
    assert counts["reject_broken"] == 1


def test_cli_growth_review_demo_behavior(capsys) -> None:
    assert main(["--growth-review-demo"]) == 0

    output = capsys.readouterr().out
    assert "Growth Lab demo: KnowledgeSeed review pipeline" in output
    assert "Duplicate checks:" in output
    assert "Conflict checks:" in output
    assert "Review decisions:" in output
    assert "merge_duplicate" in output
