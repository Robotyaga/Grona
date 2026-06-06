from grona import (
    InferenceReview,
    InferenceReviewPolicy,
    InferenceTrace,
    RenderedPrompt,
    ReviewedTraceBuildResult,
    ReviewedTraceTrainingExampleBuilder,
    TrainingDataExporter,
    build_training_examples_from_reviews,
    skipped_reviewed_trace_results,
    training_examples_from_build_results,
)


def make_trace(trace_id: str = "trace:1", response_text: str = "Original answer.") -> InferenceTrace:
    prompt = RenderedPrompt(
        template_name="training_example_review",
        system_prompt="Review conservatively.",
        user_prompt="Task:\nCreate a trace answer.\n\nContext:\nVisible context.",
        metadata={"license": "internal-test-license"},
    )
    return InferenceTrace(
        trace_id=trace_id,
        created_at="2026-01-01T00:00:00+00:00",
        task="Create a trace answer.",
        prompt=prompt,
        adapter_name="static-local-llm",
        model="static-demo",
        response_text=response_text,
        routing_summary="Task routed with selected modules: code.",
        selected_modules=("code", "documents"),
        context_sources=("demo-memory",),
        metadata={"domains": ("code",), "capabilities": ("routing",)},
    )


def make_review(
    status: str = "accepted",
    trace_id: str = "trace:1",
    review_id: str = "review:1",
    rating: int | None = 5,
    quality_flags: tuple[str, ...] = ("useful",),
    corrected_response: str = "",
) -> InferenceReview:
    return InferenceReview(
        review_id=review_id,
        trace_id=trace_id,
        created_at="2026-01-01T00:00:00+00:00",
        reviewer="human",
        status=status,
        rating=rating,
        quality_flags=quality_flags,
        notes="Reviewed by a human.",
        corrected_response=corrected_response,
        metadata={"review_source": "test"},
    )


def test_reviewed_trace_build_result_creation() -> None:
    result = ReviewedTraceBuildResult(
        trace_id="trace:1",
        review_id="review:1",
        created=False,
        reasons=("skipped",),
        metadata={"key": "value"},
    )

    assert result.created is False
    assert result.training_example is None
    assert result.to_dict()["reasons"] == ["skipped"]
    assert "Created: False" in result.to_text()


def test_accepted_review_creates_training_example() -> None:
    result = ReviewedTraceTrainingExampleBuilder().build(make_trace(), make_review())

    assert result.created is True
    assert result.training_example is not None
    example = result.training_example
    assert example.instruction == "Create a trace answer."
    assert example.output == "Original answer."
    assert example.source == "reviewed_inference_trace"
    assert example.validation_status == "reviewed"
    assert example.license == "internal-test-license"


def test_corrected_review_uses_corrected_response() -> None:
    result = ReviewedTraceTrainingExampleBuilder().build(
        make_trace(response_text="Bad original answer."),
        make_review(
            status="corrected",
            rating=4,
            quality_flags=("incomplete",),
            corrected_response="Corrected answer for training candidate.",
        ),
    )

    assert result.created is True
    assert result.training_example is not None
    assert result.training_example.output == "Corrected answer for training candidate."
    assert "corrected_response" in " ".join(result.reasons)


def test_rejected_unsafe_and_not_reviewed_reviews_do_not_create_examples() -> None:
    builder = ReviewedTraceTrainingExampleBuilder()

    rejected = builder.build(make_trace(), make_review(status="rejected", rating=1))
    unsafe = builder.build(
        make_trace(),
        make_review(status="unsafe", rating=1, quality_flags=("unsafe",)),
    )
    not_reviewed = builder.build(make_trace(), make_review(status="not_reviewed", rating=None))

    assert rejected.created is False
    assert unsafe.created is False
    assert not_reviewed.created is False
    assert rejected.training_example is None
    assert unsafe.training_example is None
    assert not_reviewed.training_example is None


def test_missing_review_and_missing_trace_are_skipped() -> None:
    trace = make_trace("trace:has-no-review")
    review = make_review(trace_id="trace:has-no-trace", review_id="review:orphan")

    results = build_training_examples_from_reviews((trace,), (review,), InferenceReviewPolicy())

    assert len(results) == 2
    assert results[0].trace_id == "trace:has-no-review"
    assert results[0].created is False
    assert "matching inference review" in " ".join(results[0].reasons)
    assert results[1].review_id == "review:orphan"
    assert results[1].created is False
    assert "matching inference trace" in " ".join(results[1].reasons)


def test_provenance_and_review_metadata_are_preserved() -> None:
    result = ReviewedTraceTrainingExampleBuilder().build(make_trace(), make_review())

    assert result.training_example is not None
    provenance = result.training_example.provenance
    metadata = result.training_example.metadata
    assert provenance["trace_id"] == "trace:1"
    assert provenance["review_id"] == "review:1"
    assert provenance["adapter_name"] == "static-local-llm"
    assert provenance["model"] == "static-demo"
    assert provenance["prompt_template_name"] == "training_example_review"
    assert metadata["review_status"] == "accepted"
    assert metadata["rating"] == 5
    assert metadata["quality_flags"] == ["useful"]
    assert metadata["reviewer"] == "human"
    assert metadata["review_notes"] == "Reviewed by a human."


def test_batch_builder_uses_deterministic_ordering() -> None:
    traces = (make_trace("trace:b"), make_trace("trace:a"))
    reviews = (
        make_review(trace_id="trace:a", review_id="review:a"),
        make_review(trace_id="trace:b", review_id="review:b2"),
        make_review(trace_id="trace:b", review_id="review:b1"),
    )

    results = build_training_examples_from_reviews(traces, reviews)

    assert [(result.trace_id, result.review_id) for result in results] == [
        ("trace:b", "review:b1"),
        ("trace:b", "review:b2"),
        ("trace:a", "review:a"),
    ]
    assert len(training_examples_from_build_results(results)) == 3
    assert skipped_reviewed_trace_results(results) == ()


def test_training_data_exporter_accepts_reviewed_trace_examples() -> None:
    results = build_training_examples_from_reviews((make_trace(),), (make_review(),))
    examples = training_examples_from_build_results(results)

    dataset = TrainingDataExporter().build_dataset(
        "reviewed-traces",
        "Reviewed trace examples.",
        examples,
        created_at="2026-01-01T00:00:00+00:00",
    )

    assert dataset.count() == 1
    assert dataset.examples[0].source == "reviewed_inference_trace"
    assert "trace:1" in dataset.to_native_jsonl()


def test_reviewed_trace_training_cli_output(capsys) -> None:  # type: ignore[no-untyped-def]
    from grona.entrypoint import main as entrypoint_main
    from grona.reviewed_trace_training_cli import format_reviewed_trace_training_demo

    text = format_reviewed_trace_training_demo()

    assert "Reviewed trace training demo" in text
    assert "Created examples: 2" in text
    assert "Skipped traces/reviews: 2" in text
    assert "Native JSONL preview" in text

    assert entrypoint_main(("--reviewed-trace-training-demo",)) == 0
    captured = capsys.readouterr()
    assert "Reviewed trace training demo" in captured.out
