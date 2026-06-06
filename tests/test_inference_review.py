from grona import (
    InferenceReview,
    InferenceReviewConfig,
    InferenceReviewPolicy,
    InferenceReviewSummary,
    InMemoryInferenceReviewStore,
    JsonlInferenceReviewStore,
)
from grona.entrypoint import main as entrypoint_main
from grona.inference_review import create_demo_inference_review_workflow
from grona.inference_review_cli import format_inference_review_demo


def make_review(**overrides: object) -> InferenceReview:
    values = {
        "review_id": "review:1",
        "trace_id": "trace:1",
        "created_at": "2026-01-01T00:00:00+00:00",
        "reviewer": "human",
        "status": "accepted",
        "rating": 5,
        "quality_flags": ("useful",),
        "notes": "Looks usable.",
        "corrected_response": "",
        "metadata": {"source": "test"},
    }
    values.update(overrides)
    return InferenceReview(**values)


def test_inference_review_json_roundtrip() -> None:
    review = make_review(quality_flags=("useful", "good_structure", "useful"))

    restored = InferenceReview.from_json(review.to_json())

    assert restored.to_dict() == review.to_dict()
    assert restored.quality_flags == ("useful", "good_structure")


def test_policy_accepts_high_rated_accepted_review() -> None:
    decision = InferenceReviewPolicy().evaluate(make_review())

    assert decision.eligible_for_training is True
    assert decision.eligible_for_knowledge_seed is True
    assert decision.eligible_for_benchmark_reference is True
    assert "accepted review" in decision.reasons[0]


def test_policy_blocks_rejected_not_reviewed_and_unsafe_reviews() -> None:
    policy = InferenceReviewPolicy()

    rejected = policy.evaluate(make_review(status="rejected", rating=1))
    not_reviewed = policy.evaluate(make_review(status="not_reviewed", rating=None))
    unsafe = policy.evaluate(
        make_review(status="accepted", rating=5, quality_flags=("unsafe",))
    )

    assert rejected.eligible_for_training is False
    assert not_reviewed.eligible_for_training is False
    assert unsafe.eligible_for_training is False
    assert "unsafe" in unsafe.reasons[0]


def test_policy_handles_corrected_review_requirements() -> None:
    policy = InferenceReviewPolicy()

    missing_correction = policy.evaluate(
        make_review(status="corrected", rating=4, corrected_response="")
    )
    corrected = policy.evaluate(
        make_review(
            status="corrected",
            rating=4,
            quality_flags=("incomplete",),
            corrected_response="Use this corrected answer instead.",
        )
    )
    disabled = InferenceReviewPolicy(
        InferenceReviewConfig(allow_corrected_as_accepted=False)
    ).evaluate(
        make_review(
            status="corrected",
            rating=4,
            corrected_response="Use this corrected answer instead.",
        )
    )

    assert missing_correction.eligible_for_training is False
    assert "corrected_response" in " ".join(missing_correction.reasons)
    assert corrected.eligible_for_training is True
    assert disabled.eligible_for_training is False


def test_in_memory_review_store() -> None:
    review = make_review()
    other = make_review(review_id="review:2", trace_id="trace:2")
    store = InMemoryInferenceReviewStore()

    store.add(review)
    store.add(other)

    assert store.count() == 2
    assert store.list() == (review, other)
    assert store.get("review:1") == review
    assert store.find_by_trace_id("trace:1") == (review,)
    store.clear()
    assert store.count() == 0


def test_jsonl_review_store(tmp_path) -> None:  # type: ignore[no-untyped-def]
    review = make_review()
    other = make_review(review_id="review:2", trace_id="trace:1")
    store = JsonlInferenceReviewStore(tmp_path / "reviews.jsonl")

    store.add(review)
    store.add(other)

    assert store.count() == 2
    assert [item.to_dict() for item in store.list()] == [review.to_dict(), other.to_dict()]
    assert store.get("review:1").to_dict() == review.to_dict()  # type: ignore[union-attr]
    assert len(store.find_by_trace_id("trace:1")) == 2
    store.clear()
    assert store.count() == 0


def test_inference_review_summary_counts_policy_eligible_reviews() -> None:
    reviews = (
        make_review(status="accepted", rating=5),
        make_review(
            review_id="review:2",
            status="corrected",
            rating=4,
            corrected_response="Corrected answer.",
        ),
        make_review(review_id="review:3", status="unsafe", rating=1, quality_flags=("unsafe",)),
        make_review(review_id="review:4", status="rejected", rating=1),
    )

    summary = InferenceReviewSummary.from_reviews(reviews)

    assert summary.total_reviews == 4
    assert summary.status_counts["accepted"] == 1
    assert summary.status_counts["corrected"] == 1
    assert summary.eligible_for_training_count == 2
    assert summary.unsafe_count == 1
    assert summary.corrected_count == 1
    assert summary.rejected_count == 1
    assert summary.average_rating == 3.0


def test_demo_workflow_creates_traces_reviews_decisions_and_summary() -> None:
    result = create_demo_inference_review_workflow()

    assert len(result.traces) == 3
    assert len(result.reviews) == 3
    assert len(result.decisions) == 3
    assert result.summary.total_reviews == 3
    assert result.summary.eligible_for_training_count == 2


def test_inference_review_cli_output_and_entrypoint(capsys) -> None:  # type: ignore[no-untyped-def]
    text = format_inference_review_demo()

    assert "Inference review demo" in text
    assert "deterministic offline review" in text
    assert "review:accepted-demo" in text
    assert "Eligible for training: True" in text

    assert entrypoint_main(("--inference-review-demo",)) == 0
    captured = capsys.readouterr()
    assert "Inference review demo" in captured.out
