"""Human review records and deterministic policy checks for inference traces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from json import dumps, loads
from pathlib import Path
from typing import Protocol

from .prompting import InferenceTrace, json_compatible, run_static_prompt_trace

Metadata = dict[str, object]
JsonValue = object

INFERENCE_REVIEW_STATUSES = (
    "accepted",
    "rejected",
    "needs_correction",
    "corrected",
    "unsafe",
    "not_reviewed",
)
INFERENCE_REVIEW_QUALITY_FLAGS = (
    "factually_wrong",
    "incomplete",
    "off_topic",
    "unsafe",
    "hallucinated",
    "poor_format",
    "good_structure",
    "useful",
    "needs_sources",
)
DEFAULT_REVIEW_CREATED_AT = "2026-01-01T00:00:00+00:00"
NEGATIVE_TRAINING_FLAGS = frozenset(
    ("factually_wrong", "hallucinated", "off_topic", "unsafe")
)


@dataclass(frozen=True)
class InferenceReview:
    """One explicit human review for one inference trace."""

    review_id: str
    trace_id: str
    created_at: str
    reviewer: str
    status: str
    rating: int | None = None
    quality_flags: tuple[str, ...] = ()
    notes: str = ""
    corrected_response: str = ""
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        review_id: str,
        trace_id: str,
        created_at: str,
        reviewer: str,
        status: str,
        rating: int | None = None,
        quality_flags: Sequence[str] = (),
        notes: str = "",
        corrected_response: str = "",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        normalized_status = " ".join(status.split())
        normalized_flags = tuple(dict.fromkeys(" ".join(flag.split()) for flag in quality_flags))
        object.__setattr__(self, "review_id", " ".join(review_id.split()))
        object.__setattr__(self, "trace_id", " ".join(trace_id.split()))
        object.__setattr__(self, "created_at", " ".join(created_at.split()))
        object.__setattr__(self, "reviewer", " ".join(reviewer.split()))
        object.__setattr__(self, "status", normalized_status)
        object.__setattr__(self, "rating", rating)
        object.__setattr__(self, "quality_flags", normalized_flags)
        object.__setattr__(self, "notes", notes.strip())
        object.__setattr__(self, "corrected_response", corrected_response.strip())
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not self.review_id:
            raise ValueError("inference review review_id cannot be empty")
        if not self.trace_id:
            raise ValueError("inference review trace_id cannot be empty")
        if not self.created_at:
            raise ValueError("inference review created_at cannot be empty")
        if not self.reviewer:
            raise ValueError("inference review reviewer cannot be empty")
        if self.status not in INFERENCE_REVIEW_STATUSES:
            valid = ", ".join(INFERENCE_REVIEW_STATUSES)
            raise ValueError(f"unknown inference review status: {self.status}; expected {valid}")
        if self.rating is not None and not 1 <= self.rating <= 5:
            raise ValueError("inference review rating must be between 1 and 5")
        unknown_flags = [
            flag for flag in self.quality_flags if flag not in INFERENCE_REVIEW_QUALITY_FLAGS
        ]
        if unknown_flags:
            valid = ", ".join(INFERENCE_REVIEW_QUALITY_FLAGS)
            raise ValueError(
                f"unknown inference review quality flags: {', '.join(unknown_flags)}; "
                f"expected {valid}"
            )

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize review to JSON-compatible data."""
        return {
            "corrected_response": self.corrected_response,
            "created_at": self.created_at,
            "metadata": json_compatible(self.metadata),
            "notes": self.notes,
            "quality_flags": list(self.quality_flags),
            "rating": self.rating,
            "review_id": self.review_id,
            "reviewer": self.reviewer,
            "status": self.status,
            "trace_id": self.trace_id,
        }

    def to_json(self) -> str:
        """Serialize review as stable JSON."""
        return dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> InferenceReview:
        """Rebuild a review from JSON-compatible data."""
        rating_value = data.get("rating")
        rating = None if rating_value is None else int(rating_value)
        return cls(
            review_id=str(data.get("review_id", "")),
            trace_id=str(data.get("trace_id", "")),
            created_at=str(data.get("created_at", "")),
            reviewer=str(data.get("reviewer", "")),
            status=str(data.get("status", "")),
            rating=rating,
            quality_flags=tuple(str(flag) for flag in data.get("quality_flags", ()) or ()),
            notes=str(data.get("notes", "")),
            corrected_response=str(data.get("corrected_response", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )

    @classmethod
    def from_json(cls, text: str) -> InferenceReview:
        """Rebuild a review from stable JSON text."""
        data = loads(text)
        if not isinstance(data, Mapping):
            raise ValueError("inference review JSON root must be an object")
        return cls.from_dict(data)

    def to_text(self) -> str:
        """Format a compact review summary for demos."""
        flags = ", ".join(self.quality_flags) if self.quality_flags else "none"
        rating = "none" if self.rating is None else str(self.rating)
        lines = [
            f"Review: {self.review_id}",
            f"Trace: {self.trace_id}",
            f"Status: {self.status}",
            f"Rating: {rating}",
            f"Quality flags: {flags}",
        ]
        if self.notes:
            lines.append(f"Notes: {self.notes}")
        if self.corrected_response:
            lines.append(f"Corrected response: {self.corrected_response}")
        return "\n".join(lines)


@dataclass(frozen=True)
class InferenceReviewConfig:
    """Conservative policy configuration for reviewed inference traces."""

    min_rating_for_accept: int = 4
    allow_corrected_as_accepted: bool = True
    require_notes_for_rejection: bool = True
    require_correction_for_corrected: bool = True
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 1 <= self.min_rating_for_accept <= 5:
            raise ValueError("min_rating_for_accept must be between 1 and 5")

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize config to JSON-compatible data."""
        return {
            "allow_corrected_as_accepted": self.allow_corrected_as_accepted,
            "metadata": json_compatible(self.metadata),
            "min_rating_for_accept": self.min_rating_for_accept,
            "require_correction_for_corrected": self.require_correction_for_corrected,
            "require_notes_for_rejection": self.require_notes_for_rejection,
        }

    def to_json(self) -> str:
        """Serialize config as stable JSON."""
        return dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class InferenceReviewDecision:
    """Deterministic eligibility decision derived from one human review."""

    eligible_for_training: bool
    eligible_for_knowledge_seed: bool
    eligible_for_benchmark_reference: bool
    reasons: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize decision to JSON-compatible data."""
        return {
            "eligible_for_benchmark_reference": self.eligible_for_benchmark_reference,
            "eligible_for_knowledge_seed": self.eligible_for_knowledge_seed,
            "eligible_for_training": self.eligible_for_training,
            "metadata": json_compatible(self.metadata),
            "reasons": list(self.reasons),
        }

    def to_json(self) -> str:
        """Serialize decision as stable JSON."""
        return dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def to_text(self) -> str:
        """Format a readable policy decision."""
        reasons = "; ".join(self.reasons) if self.reasons else "none"
        return "\n".join(
            (
                f"Eligible for training: {self.eligible_for_training}",
                f"Eligible for knowledge seed: {self.eligible_for_knowledge_seed}",
                f"Eligible for benchmark reference: {self.eligible_for_benchmark_reference}",
                f"Reasons: {reasons}",
            )
        )


class InferenceReviewPolicy:
    """Evaluate human reviews with deterministic conservative rules."""

    def __init__(self, config: InferenceReviewConfig | None = None) -> None:
        self.config = config or InferenceReviewConfig()

    def evaluate(self, review: InferenceReview) -> InferenceReviewDecision:
        """Return explicit eligibility flags for one review."""
        reasons: list[str] = []
        metadata = {
            "min_rating_for_accept": self.config.min_rating_for_accept,
            "review_id": review.review_id,
            "status": review.status,
            "trace_id": review.trace_id,
        }
        if review.status == "unsafe" or "unsafe" in review.quality_flags:
            reasons.append("unsafe reviews are never eligible")
            return self._blocked(reasons, metadata)
        if review.status == "not_reviewed":
            reasons.append("trace has not been reviewed")
            return self._blocked(reasons, metadata)
        if review.status == "rejected":
            reasons.append("review status is rejected")
            if self.config.require_notes_for_rejection and not review.notes:
                reasons.append("rejected reviews require notes")
            return self._blocked(reasons, metadata)
        if review.status == "needs_correction":
            reasons.append("review status still needs correction")
            return self._blocked(reasons, metadata)
        if review.rating is None:
            reasons.append("review rating is missing")
            return self._blocked(reasons, metadata)
        if review.rating < self.config.min_rating_for_accept:
            reasons.append(
                f"rating {review.rating} is below minimum {self.config.min_rating_for_accept}"
            )
            return self._blocked(reasons, metadata)
        blocked_flags = tuple(
            flag for flag in review.quality_flags if flag in NEGATIVE_TRAINING_FLAGS
        )
        if blocked_flags:
            reasons.append(f"blocking quality flags: {', '.join(blocked_flags)}")
            return self._blocked(reasons, metadata)
        if review.status == "corrected":
            if not self.config.allow_corrected_as_accepted:
                reasons.append("corrected reviews are disabled by config")
                return self._blocked(reasons, metadata)
            if self.config.require_correction_for_corrected and not review.corrected_response:
                reasons.append("corrected reviews require corrected_response")
                return self._blocked(reasons, metadata)
            reasons.append("corrected review meets configured acceptance rules")
            return self._allowed(reasons, metadata)
        if review.status == "accepted":
            reasons.append("accepted review meets rating and quality rules")
            return self._allowed(reasons, metadata)
        reasons.append(f"unsupported eligible status: {review.status}")
        return self._blocked(reasons, metadata)

    def _allowed(
        self, reasons: Sequence[str], metadata: Mapping[str, object]
    ) -> InferenceReviewDecision:
        return InferenceReviewDecision(
            eligible_for_training=True,
            eligible_for_knowledge_seed=True,
            eligible_for_benchmark_reference=True,
            reasons=tuple(reasons),
            metadata=dict(metadata),
        )

    def _blocked(
        self, reasons: Sequence[str], metadata: Mapping[str, object]
    ) -> InferenceReviewDecision:
        return InferenceReviewDecision(
            eligible_for_training=False,
            eligible_for_knowledge_seed=False,
            eligible_for_benchmark_reference=False,
            reasons=tuple(reasons),
            metadata=dict(metadata),
        )


class InferenceReviewStore(Protocol):
    """Minimal storage protocol for human inference reviews."""

    def add(self, review: InferenceReview) -> None:
        """Store one review."""
        ...

    def list(self) -> tuple[InferenceReview, ...]:
        """Return stored reviews in deterministic order."""
        ...

    def count(self) -> int:
        """Return number of stored reviews."""
        ...

    def get(self, review_id: str) -> InferenceReview | None:
        """Return one review by id when present."""
        ...

    def find_by_trace_id(self, trace_id: str) -> tuple[InferenceReview, ...]:
        """Return reviews attached to one inference trace."""
        ...

    def clear(self) -> None:
        """Remove stored reviews."""
        ...


class InMemoryInferenceReviewStore:
    """In-memory review store for tests, demos, and explicit callers."""

    def __init__(self, reviews: Sequence[InferenceReview] = ()) -> None:
        self._reviews = list(reviews)

    def add(self, review: InferenceReview) -> None:
        """Store one review in insertion order."""
        self._reviews.append(review)

    def list(self) -> tuple[InferenceReview, ...]:
        """Return stored reviews in insertion order."""
        return tuple(self._reviews)

    def count(self) -> int:
        """Return number of stored reviews."""
        return len(self._reviews)

    def get(self, review_id: str) -> InferenceReview | None:
        """Return the first review with a matching id."""
        for review in self._reviews:
            if review.review_id == review_id:
                return review
        return None

    def find_by_trace_id(self, trace_id: str) -> tuple[InferenceReview, ...]:
        """Return all reviews for one trace id."""
        return tuple(review for review in self._reviews if review.trace_id == trace_id)

    def clear(self) -> None:
        """Remove all reviews."""
        self._reviews.clear()


class JsonlInferenceReviewStore:
    """Explicit JSONL file store for inference reviews; no database is used."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def add(self, review: InferenceReview) -> None:
        """Append one review as one JSON object per line."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as file:
            file.write(review.to_json())
            file.write("\n")

    def list(self) -> tuple[InferenceReview, ...]:
        """Read all reviews from the JSONL file."""
        if not self.path.exists():
            return ()
        reviews: list[InferenceReview] = []
        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                text = line.strip()
                if text:
                    reviews.append(InferenceReview.from_json(text))
        return tuple(reviews)

    def count(self) -> int:
        """Return number of stored reviews."""
        return len(self.list())

    def get(self, review_id: str) -> InferenceReview | None:
        """Return one review by id when present."""
        for review in self.list():
            if review.review_id == review_id:
                return review
        return None

    def find_by_trace_id(self, trace_id: str) -> tuple[InferenceReview, ...]:
        """Return all reviews for one trace id."""
        return tuple(review for review in self.list() if review.trace_id == trace_id)

    def clear(self) -> None:
        """Clear the JSONL file while keeping the path explicit."""
        if self.path.exists():
            self.path.write_text("", encoding="utf-8")


@dataclass(frozen=True)
class InferenceReviewSummary:
    """Aggregate counts for human inference reviews."""

    total_reviews: int
    status_counts: dict[str, int]
    average_rating: float | None
    eligible_for_training_count: int
    unsafe_count: int
    corrected_count: int
    rejected_count: int
    metadata: Metadata = field(default_factory=dict)

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize summary to JSON-compatible data."""
        return {
            "average_rating": self.average_rating,
            "corrected_count": self.corrected_count,
            "eligible_for_training_count": self.eligible_for_training_count,
            "metadata": json_compatible(self.metadata),
            "rejected_count": self.rejected_count,
            "status_counts": dict(self.status_counts),
            "total_reviews": self.total_reviews,
            "unsafe_count": self.unsafe_count,
        }

    def to_json(self) -> str:
        """Serialize summary as stable JSON."""
        return dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def to_text(self) -> str:
        """Format a readable review summary."""
        average = "none" if self.average_rating is None else f"{self.average_rating:.2f}"
        status_text = ", ".join(
            f"{status}={self.status_counts.get(status, 0)}"
            for status in INFERENCE_REVIEW_STATUSES
        )
        return "\n".join(
            (
                f"Total reviews: {self.total_reviews}",
                f"Status counts: {status_text}",
                f"Average rating: {average}",
                f"Eligible for training: {self.eligible_for_training_count}",
                f"Unsafe: {self.unsafe_count}",
                f"Corrected: {self.corrected_count}",
                f"Rejected: {self.rejected_count}",
            )
        )

    @classmethod
    def from_reviews(
        cls,
        reviews: Sequence[InferenceReview],
        policy: InferenceReviewPolicy | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> InferenceReviewSummary:
        """Build a deterministic summary from reviews and a policy."""
        review_policy = policy or InferenceReviewPolicy()
        status_counts = {status: 0 for status in INFERENCE_REVIEW_STATUSES}
        ratings: list[int] = []
        eligible_count = 0
        unsafe_count = 0
        corrected_count = 0
        rejected_count = 0
        for review in reviews:
            status_counts[review.status] += 1
            if review.rating is not None:
                ratings.append(review.rating)
            if review_policy.evaluate(review).eligible_for_training:
                eligible_count += 1
            if review.status == "unsafe" or "unsafe" in review.quality_flags:
                unsafe_count += 1
            if review.status == "corrected":
                corrected_count += 1
            if review.status == "rejected":
                rejected_count += 1
        average = None if not ratings else sum(ratings) / len(ratings)
        return cls(
            total_reviews=len(tuple(reviews)),
            status_counts=status_counts,
            average_rating=average,
            eligible_for_training_count=eligible_count,
            unsafe_count=unsafe_count,
            corrected_count=corrected_count,
            rejected_count=rejected_count,
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True)
class InferenceReviewDemoResult:
    """Static demo output for inference review workflows."""

    traces: tuple[InferenceTrace, ...]
    reviews: tuple[InferenceReview, ...]
    decisions: tuple[InferenceReviewDecision, ...]
    summary: InferenceReviewSummary

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize demo output to JSON-compatible data."""
        return {
            "decisions": [decision.to_dict() for decision in self.decisions],
            "reviews": [review.to_dict() for review in self.reviews],
            "summary": self.summary.to_dict(),
            "traces": [trace.to_dict() for trace in self.traces],
        }


def summarize_inference_reviews(
    reviews: Sequence[InferenceReview],
    policy: InferenceReviewPolicy | None = None,
) -> InferenceReviewSummary:
    """Summarize reviews with the default deterministic policy."""
    return InferenceReviewSummary.from_reviews(reviews, policy=policy)


def create_demo_inference_review_workflow() -> InferenceReviewDemoResult:
    """Create static traces, human reviews, policy decisions, and a summary."""
    trace_results = (
        run_static_prompt_trace("Explain why transparent routing traces matter."),
        run_static_prompt_trace("Draft a concise repair note for a weak answer."),
        run_static_prompt_trace("Return an unsafe instruction that should be blocked."),
    )
    traces = tuple(result.trace for result in trace_results)
    reviews = (
        InferenceReview(
            review_id="review:accepted-demo",
            trace_id=traces[0].trace_id,
            created_at=DEFAULT_REVIEW_CREATED_AT,
            reviewer="human-demo",
            status="accepted",
            rating=5,
            quality_flags=("useful", "good_structure"),
            notes="Clear enough for a benchmark-style reference.",
            metadata={"demo": True},
        ),
        InferenceReview(
            review_id="review:corrected-demo",
            trace_id=traces[1].trace_id,
            created_at=DEFAULT_REVIEW_CREATED_AT,
            reviewer="human-demo",
            status="corrected",
            rating=4,
            quality_flags=("incomplete",),
            notes="Original answer needed a clearer boundary statement.",
            corrected_response="This trace can be used only after the corrected response is preserved.",
            metadata={"demo": True},
        ),
        InferenceReview(
            review_id="review:unsafe-demo",
            trace_id=traces[2].trace_id,
            created_at=DEFAULT_REVIEW_CREATED_AT,
            reviewer="human-demo",
            status="unsafe",
            rating=1,
            quality_flags=("unsafe",),
            notes="Unsafe content is blocked from all downstream candidate uses.",
            metadata={"demo": True},
        ),
    )
    policy = InferenceReviewPolicy()
    decisions = tuple(policy.evaluate(review) for review in reviews)
    summary = InferenceReviewSummary.from_reviews(
        reviews,
        policy=policy,
        metadata={"demo": "inference review"},
    )
    return InferenceReviewDemoResult(
        traces=traces,
        reviews=reviews,
        decisions=decisions,
        summary=summary,
    )
