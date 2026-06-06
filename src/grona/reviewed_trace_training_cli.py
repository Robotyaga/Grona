"""Console demo for reviewed trace to training example candidates."""

from __future__ import annotations

from collections.abc import Sequence

from .context import ContextBuilder
from .defaults import create_default_registry
from .inference_review import DEFAULT_REVIEW_CREATED_AT, InferenceReview, InferenceReviewPolicy
from .prompting import run_static_prompt_trace
from .reviewed_trace_training import (
    build_training_examples_from_reviews,
    skipped_reviewed_trace_results,
    training_examples_from_build_results,
)
from .router import Router
from .training import TrainingDataExporter


def create_reviewed_trace_training_demo() -> tuple[object, ...]:
    """Create deterministic traces, reviews, build results, and a dataset."""
    tasks = (
        "Explain why reviewed inference traces should preserve provenance.",
        "Draft a corrected answer for an incomplete trace.",
        "Produce a rejected answer that should not become training data.",
        "Produce unsafe output that must be blocked from training data.",
    )
    router = Router(create_default_registry(), top_k=2)
    traces = []
    for task in tasks:
        decision = router.route(task)
        context_items = ContextBuilder().build(decision, task)
        result = run_static_prompt_trace(
            task,
            routing_decision=decision,
            context_items=context_items,
            workspace_metadata={"workspace": "default", "demo": "reviewed_trace_training"},
        )
        traces.append(result.trace)
    reviews = (
        InferenceReview(
            review_id="review-train:accepted",
            trace_id=traces[0].trace_id,
            created_at=DEFAULT_REVIEW_CREATED_AT,
            reviewer="human-demo",
            status="accepted",
            rating=5,
            quality_flags=("useful", "good_structure"),
            notes="Accepted for candidate training export testing.",
        ),
        InferenceReview(
            review_id="review-train:corrected",
            trace_id=traces[1].trace_id,
            created_at=DEFAULT_REVIEW_CREATED_AT,
            reviewer="human-demo",
            status="corrected",
            rating=4,
            quality_flags=("incomplete",),
            notes="Use the corrected response, not the original weak output.",
            corrected_response="Corrected traces must preserve review metadata before export.",
        ),
        InferenceReview(
            review_id="review-train:rejected",
            trace_id=traces[2].trace_id,
            created_at=DEFAULT_REVIEW_CREATED_AT,
            reviewer="human-demo",
            status="rejected",
            rating=1,
            quality_flags=("off_topic",),
            notes="Rejected traces stay out of training candidates.",
        ),
        InferenceReview(
            review_id="review-train:unsafe",
            trace_id=traces[3].trace_id,
            created_at=DEFAULT_REVIEW_CREATED_AT,
            reviewer="human-demo",
            status="unsafe",
            rating=1,
            quality_flags=("unsafe",),
            notes="Unsafe traces are blocked from all downstream candidate uses.",
        ),
    )
    results = build_training_examples_from_reviews(
        tuple(traces),
        reviews,
        policy=InferenceReviewPolicy(),
    )
    examples = training_examples_from_build_results(results)
    dataset = TrainingDataExporter().build_dataset(
        "reviewed-trace-training-demo",
        "Deterministic reviewed trace training candidates.",
        examples,
        created_at=DEFAULT_REVIEW_CREATED_AT,
        metadata={"demo": "reviewed_trace_training"},
    )
    return tuple(traces), reviews, results, dataset


def format_reviewed_trace_training_demo() -> str:
    """Return deterministic demo text for reviewed trace training candidates."""
    _traces, _reviews, results, dataset = create_reviewed_trace_training_demo()
    created = training_examples_from_build_results(results)
    skipped = skipped_reviewed_trace_results(results)
    lines = [
        "Reviewed trace training demo",
        "Execution: deterministic offline trace review only; no LLM calls, APIs, downloads, files, or training.",
        "",
        f"Created examples: {len(created)}",
        f"Skipped traces/reviews: {len(skipped)}",
        "",
        dataset.to_text(),
        "",
        "Build results:",
    ]
    for result in results:
        lines.append(result.to_text())
        lines.append("")
    if dataset.count():
        lines.extend(("Native JSONL preview:", dataset.to_native_jsonl()))
    return "\n".join(lines).strip()


def main(argv: Sequence[str] | None = None) -> int:
    """Print the deterministic reviewed trace training demo."""
    _ = argv
    print(format_reviewed_trace_training_demo())
    return 0
