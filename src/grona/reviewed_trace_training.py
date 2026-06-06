"""Build training example candidates from reviewed inference traces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .inference_review import InferenceReview, InferenceReviewPolicy
from .prompting import InferenceTrace, json_compatible
from .training import TrainingExample

Metadata = dict[str, object]
JsonValue = object
DEFAULT_REVIEWED_TRACE_LICENSE = "internal-reviewed-trace-demo"


@dataclass(frozen=True)
class ReviewedTraceBuildResult:
    """Result of trying to build one TrainingExample from one reviewed trace."""

    trace_id: str
    review_id: str
    created: bool
    training_example: TrainingExample | None = None
    reasons: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize the build result to JSON-compatible data."""
        return {
            "created": self.created,
            "metadata": json_compatible(self.metadata),
            "reasons": list(self.reasons),
            "review_id": self.review_id,
            "trace_id": self.trace_id,
            "training_example": (
                self.training_example.to_native_record()
                if self.training_example is not None
                else None
            ),
        }

    def to_text(self) -> str:
        """Format a compact build result for demos."""
        reasons = "; ".join(self.reasons) if self.reasons else "none"
        lines = [
            f"Trace: {self.trace_id or 'missing'}",
            f"Review: {self.review_id or 'missing'}",
            f"Created: {self.created}",
            f"Reasons: {reasons}",
        ]
        if self.training_example is not None:
            lines.extend(
                (
                    "Training example preview:",
                    f"Instruction: {self.training_example.instruction}",
                    f"Output: {self.training_example.output}",
                )
            )
        return "\n".join(lines)


class ReviewedTraceTrainingExampleBuilder:
    """Create TrainingExample candidates only from eligible reviewed traces."""

    def __init__(self, policy: InferenceReviewPolicy | None = None) -> None:
        self.policy = policy or InferenceReviewPolicy()

    def build(
        self,
        trace: InferenceTrace,
        review: InferenceReview,
    ) -> ReviewedTraceBuildResult:
        """Evaluate one trace/review pair and build an example when allowed."""
        if trace.trace_id != review.trace_id:
            return ReviewedTraceBuildResult(
                trace_id=trace.trace_id,
                review_id=review.review_id,
                created=False,
                reasons=("review trace_id does not match inference trace",),
                metadata={"review_trace_id": review.trace_id},
            )
        decision = self.policy.evaluate(review)
        reasons = list(decision.reasons)
        if not decision.eligible_for_training:
            reasons.append("review policy did not mark trace eligible for training")
            return ReviewedTraceBuildResult(
                trace_id=trace.trace_id,
                review_id=review.review_id,
                created=False,
                reasons=tuple(reasons),
                metadata={"policy_decision": decision.to_dict()},
            )
        output_text, output_reason = reviewed_trace_output_text(trace, review)
        if not output_text:
            reasons.append(output_reason)
            return ReviewedTraceBuildResult(
                trace_id=trace.trace_id,
                review_id=review.review_id,
                created=False,
                reasons=tuple(reasons),
                metadata={"policy_decision": decision.to_dict()},
            )
        reasons.append(output_reason)
        example = TrainingExample(
            instruction=trace.task or trace.prompt.user_prompt,
            input=reviewed_trace_input_text(trace),
            output=output_text,
            source="reviewed_inference_trace",
            domains=metadata_strings(trace.metadata, "domains"),
            capabilities=metadata_strings(trace.metadata, "capabilities"),
            provenance=reviewed_trace_provenance(trace, review),
            license=reviewed_trace_license(trace, review),
            validation_status="reviewed",
            metadata=reviewed_trace_metadata(review, decision.to_dict()),
        )
        return ReviewedTraceBuildResult(
            trace_id=trace.trace_id,
            review_id=review.review_id,
            created=True,
            training_example=example,
            reasons=tuple(reasons),
            metadata={"policy_decision": decision.to_dict()},
        )

    def skipped_missing_review(self, trace: InferenceTrace) -> ReviewedTraceBuildResult:
        """Return a skipped result for a trace without a matching review."""
        return ReviewedTraceBuildResult(
            trace_id=trace.trace_id,
            review_id="",
            created=False,
            reasons=("matching inference review was not found",),
            metadata={"trace_id": trace.trace_id},
        )

    def skipped_missing_trace(self, review: InferenceReview) -> ReviewedTraceBuildResult:
        """Return a skipped result for a review without a matching trace."""
        return ReviewedTraceBuildResult(
            trace_id=review.trace_id,
            review_id=review.review_id,
            created=False,
            reasons=("matching inference trace was not found",),
            metadata={"review_id": review.review_id},
        )


def build_training_examples_from_reviews(
    traces: Sequence[InferenceTrace],
    reviews: Sequence[InferenceReview],
    policy: InferenceReviewPolicy | None = None,
) -> tuple[ReviewedTraceBuildResult, ...]:
    """Build reviewed trace training candidates in deterministic trace order."""
    builder = ReviewedTraceTrainingExampleBuilder(policy)
    reviews_by_trace_id: dict[str, list[InferenceReview]] = {}
    for review in reviews:
        reviews_by_trace_id.setdefault(review.trace_id, []).append(review)
    results: list[ReviewedTraceBuildResult] = []
    seen_trace_ids: set[str] = set()
    for trace in traces:
        seen_trace_ids.add(trace.trace_id)
        matching_reviews = reviews_by_trace_id.get(trace.trace_id, [])
        if not matching_reviews:
            results.append(builder.skipped_missing_review(trace))
            continue
        for review in sorted(matching_reviews, key=lambda item: item.review_id):
            results.append(builder.build(trace, review))
    orphan_reviews = sorted(
        (review for review in reviews if review.trace_id not in seen_trace_ids),
        key=lambda item: (item.trace_id, item.review_id),
    )
    results.extend(builder.skipped_missing_trace(review) for review in orphan_reviews)
    return tuple(results)


def training_examples_from_build_results(
    results: Sequence[ReviewedTraceBuildResult],
) -> tuple[TrainingExample, ...]:
    """Return created training examples from build results."""
    return tuple(
        result.training_example
        for result in results
        if result.created and result.training_example is not None
    )


def skipped_reviewed_trace_results(
    results: Sequence[ReviewedTraceBuildResult],
) -> tuple[ReviewedTraceBuildResult, ...]:
    """Return skipped reviewed trace build results."""
    return tuple(result for result in results if not result.created)


def reviewed_trace_output_text(
    trace: InferenceTrace,
    review: InferenceReview,
) -> tuple[str, str]:
    """Select accepted or corrected output text deterministically."""
    if review.status == "corrected":
        if review.corrected_response:
            return review.corrected_response, "corrected review used corrected_response"
        return "", "corrected review is missing corrected_response"
    if review.status == "accepted":
        if trace.response_text:
            return trace.response_text, "accepted review used original trace response"
        return "", "accepted trace is missing response_text"
    return "", f"review status {review.status} is not an output source"


def reviewed_trace_input_text(trace: InferenceTrace) -> str:
    """Build model input text from the rendered prompt and visible trace metadata."""
    context_sources = ", ".join(trace.context_sources) if trace.context_sources else "none"
    sections = [
        trace.prompt.user_prompt,
        "",
        f"Prompt template: {trace.prompt.template_name}",
        f"Context sources: {context_sources}",
    ]
    if trace.routing_summary:
        sections.append(f"Routing summary: {trace.routing_summary}")
    return "\n".join(sections).strip()


def reviewed_trace_provenance(
    trace: InferenceTrace,
    review: InferenceReview,
) -> Metadata:
    """Preserve trace and review provenance for the training candidate."""
    return {
        "adapter_name": trace.adapter_name,
        "context_sources": list(trace.context_sources),
        "model": trace.model,
        "origin": "reviewed_inference_trace",
        "prompt_template_name": trace.prompt.template_name,
        "review_id": review.review_id,
        "selected_modules": list(trace.selected_modules),
        "trace_id": trace.trace_id,
    }


def reviewed_trace_metadata(
    review: InferenceReview,
    policy_decision: Mapping[str, object],
) -> Metadata:
    """Preserve human review metadata on the training candidate."""
    metadata: Metadata = {
        "policy_decision": json_compatible(policy_decision),
        "quality_flags": list(review.quality_flags),
        "rating": review.rating,
        "review_status": review.status,
        "reviewer": review.reviewer,
    }
    if review.notes:
        metadata["review_notes"] = review.notes
    metadata.update(json_compatible(review.metadata))
    return metadata


def reviewed_trace_license(trace: InferenceTrace, review: InferenceReview) -> str:
    """Return an explicit conservative license marker for reviewed traces."""
    for metadata in (review.metadata, trace.metadata, trace.prompt.metadata):
        license_value = metadata.get("license") or metadata.get("license_name")
        if isinstance(license_value, str) and license_value:
            return license_value
    return DEFAULT_REVIEWED_TRACE_LICENSE


def metadata_strings(metadata: Mapping[str, object], key: str) -> tuple[str, ...]:
    """Read a tuple of strings from trace metadata when present."""
    value = metadata.get(key)
    if isinstance(value, str) and value:
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(str(item) for item in value if str(item))
    return ()
