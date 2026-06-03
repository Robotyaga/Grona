"""Feedback records and lightweight route history stores."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from json import dumps, loads
from pathlib import Path
from typing import Any, Protocol

from .decision import RoutingDecision

JsonValue = str | int | float | bool | None | dict[str, "JsonValue"] | list["JsonValue"]
Metadata = dict[str, JsonValue]


@dataclass(frozen=True)
class FeedbackRecord:
    """A saved route outcome for later inspection and routing research."""

    task: str
    selected_modules: tuple[str, ...]
    skipped_modules: tuple[str, ...]
    confidence: float
    route_summary: str
    timestamp: str
    rating: int | None = None
    success: bool | None = None
    notes: str | None = None
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.rating is not None and not 1 <= self.rating <= 5:
            raise ValueError("rating must be between 1 and 5")

    @classmethod
    def from_decision(
        cls,
        decision: RoutingDecision,
        rating: int | None = None,
        success: bool | None = None,
        notes: str | None = None,
        metadata: Metadata | None = None,
        timestamp: str | None = None,
    ) -> FeedbackRecord:
        """Create a feedback record from a routing decision."""
        return cls(
            task=decision.task,
            selected_modules=decision.selected_names,
            skipped_modules=decision.skipped_names,
            confidence=confidence_from_decision(decision),
            route_summary=summarize_decision(decision),
            timestamp=timestamp or utc_timestamp(),
            rating=rating,
            success=success,
            notes=notes,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize the record to JSON-compatible data."""
        return {
            "task": self.task,
            "selected_modules": list(self.selected_modules),
            "skipped_modules": list(self.skipped_modules),
            "confidence": self.confidence,
            "route_summary": self.route_summary,
            "timestamp": self.timestamp,
            "rating": self.rating,
            "success": self.success,
            "notes": self.notes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeedbackRecord:
        """Deserialize a feedback record from JSON-compatible data."""
        return cls(
            task=str(data["task"]),
            selected_modules=tuple(data.get("selected_modules", ())),
            skipped_modules=tuple(data.get("skipped_modules", ())),
            confidence=float(data["confidence"]),
            route_summary=str(data["route_summary"]),
            timestamp=str(data["timestamp"]),
            rating=data.get("rating"),
            success=data.get("success"),
            notes=data.get("notes"),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass(frozen=True)
class FeedbackSummary:
    """Aggregate route history metrics."""

    total_records: int
    most_selected_modules: tuple[tuple[str, int], ...]
    average_confidence: float
    success_count: int
    failure_count: int


class FeedbackStore(Protocol):
    """Minimal interface for route feedback stores."""

    def add(self, record: FeedbackRecord) -> None:
        """Add one feedback record."""

    def list(self) -> tuple[FeedbackRecord, ...]:
        """Return all feedback records."""

    def count(self) -> int:
        """Return the number of stored records."""

    def clear(self) -> None:
        """Remove all records."""

    def summarize_by_module(self) -> dict[str, int]:
        """Count how often each module was selected."""


class InMemoryFeedbackStore:
    """Simple in-memory feedback store for tests and demos."""

    def __init__(self, records: Iterable[FeedbackRecord] = ()) -> None:
        self._records = list(records)

    def add(self, record: FeedbackRecord) -> None:
        """Add one feedback record."""
        self._records.append(record)

    def list(self) -> tuple[FeedbackRecord, ...]:
        """Return all feedback records in insertion order."""
        return tuple(self._records)

    def count(self) -> int:
        """Return the number of stored records."""
        return len(self._records)

    def clear(self) -> None:
        """Remove all records."""
        self._records.clear()

    def summarize_by_module(self) -> dict[str, int]:
        """Count how often each module was selected."""
        return summarize_by_module(self._records)


class JsonlFeedbackStore:
    """Feedback store that writes one JSON object per line."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def add(self, record: FeedbackRecord) -> None:
        """Append one feedback record as a JSONL row."""
        if self.path.parent != Path(""):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as feedback_file:
            feedback_file.write(dumps(record.to_dict(), sort_keys=True) + "\n")

    def list(self) -> tuple[FeedbackRecord, ...]:
        """Load all feedback records from the JSONL file."""
        if not self.path.exists():
            return ()
        records: list[FeedbackRecord] = []
        with self.path.open("r", encoding="utf-8") as feedback_file:
            for line in feedback_file:
                stripped = line.strip()
                if stripped:
                    records.append(FeedbackRecord.from_dict(loads(stripped)))
        return tuple(records)

    def count(self) -> int:
        """Return the number of stored records."""
        return len(self.list())

    def clear(self) -> None:
        """Remove all records while keeping the JSONL file path usable."""
        if self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def summarize_by_module(self) -> dict[str, int]:
        """Count how often each module was selected."""
        return summarize_by_module(self.list())


def summarize_feedback(records: Iterable[FeedbackRecord]) -> FeedbackSummary:
    """Summarize route history records."""
    record_tuple = tuple(records)
    total_records = len(record_tuple)
    module_counts = Counter(
        module_name for record in record_tuple for module_name in record.selected_modules
    )
    average_confidence = (
        round(sum(record.confidence for record in record_tuple) / total_records, 4)
        if total_records
        else 0.0
    )
    return FeedbackSummary(
        total_records=total_records,
        most_selected_modules=tuple(module_counts.most_common()),
        average_confidence=average_confidence,
        success_count=sum(record.success is True for record in record_tuple),
        failure_count=sum(record.success is False for record in record_tuple),
    )


def summarize_by_module(records: Iterable[FeedbackRecord]) -> dict[str, int]:
    """Count selected modules across feedback records."""
    counts = Counter(module_name for record in records for module_name in record.selected_modules)
    return dict(counts)


def confidence_from_decision(decision: RoutingDecision) -> float:
    """Estimate route confidence from selected scores versus all positive scores."""
    selected_score = sum(max(match.score, 0.0) for match in decision.selected_modules)
    all_score = selected_score + sum(max(match.score, 0.0) for match in decision.skipped_modules)
    if all_score == 0:
        return 0.0
    return round(selected_score / all_score, 4)


def summarize_decision(decision: RoutingDecision) -> str:
    """Create a compact route summary for storage."""
    selected = ", ".join(decision.selected_names) or "none"
    skipped = ", ".join(decision.skipped_names) or "none"
    return f"Selected: {selected}. Skipped: {skipped}."


def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(UTC).isoformat(timespec="seconds")
