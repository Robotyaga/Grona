"""Feedback-informed adaptive routing helpers."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from .feedback import FeedbackRecord


@dataclass(frozen=True)
class AdaptiveRoutingConfig:
    """Conservative opt-in settings for feedback-informed score adjustment."""

    enabled: bool = False
    success_boost: float = 0.15
    failure_penalty: float = 0.15
    min_feedback_records: int = 1
    max_adjustment: float = 0.5

    def __post_init__(self) -> None:
        if self.success_boost < 0:
            raise ValueError("success_boost cannot be negative")
        if self.failure_penalty < 0:
            raise ValueError("failure_penalty cannot be negative")
        if self.min_feedback_records < 0:
            raise ValueError("min_feedback_records cannot be negative")
        if self.max_adjustment < 0:
            raise ValueError("max_adjustment cannot be negative")


@dataclass(frozen=True)
class ModuleFeedbackStats:
    """Feedback history aggregated for one module."""

    module_name: str
    times_selected: int
    successes: int
    failures: int
    average_rating: float | None
    success_rate: float | None
    average_confidence: float

    @property
    def has_outcomes(self) -> bool:
        """Return whether the stats contain explicit success/failure outcomes."""
        return self.successes + self.failures > 0


def build_module_feedback_stats(
    records: Sequence[FeedbackRecord],
) -> dict[str, ModuleFeedbackStats]:
    """Aggregate feedback records into per-module routing stats."""
    buckets: dict[str, list[FeedbackRecord]] = defaultdict(list)
    for record in records:
        for module_name in record.selected_modules:
            buckets[module_name].append(record)

    stats: dict[str, ModuleFeedbackStats] = {}
    for module_name, module_records in buckets.items():
        ratings = [record.rating for record in module_records if record.rating is not None]
        successes = sum(record.success is True for record in module_records)
        failures = sum(record.success is False for record in module_records)
        outcome_count = successes + failures
        stats[module_name] = ModuleFeedbackStats(
            module_name=module_name,
            times_selected=len(module_records),
            successes=successes,
            failures=failures,
            average_rating=round(sum(ratings) / len(ratings), 4) if ratings else None,
            success_rate=round(successes / outcome_count, 4) if outcome_count else None,
            average_confidence=round(
                sum(record.confidence for record in module_records) / len(module_records), 4
            ),
        )
    return stats


def adaptive_adjustment(
    stats: ModuleFeedbackStats | None,
    config: AdaptiveRoutingConfig,
) -> float:
    """Compute a bounded score adjustment from module feedback stats."""
    if not config.enabled or stats is None or stats.times_selected < config.min_feedback_records:
        return 0.0

    adjustment = 0.0
    if stats.has_outcomes:
        outcome_count = stats.successes + stats.failures
        if stats.successes > stats.failures:
            success_signal = (stats.successes - stats.failures) / outcome_count
            adjustment += config.success_boost * success_signal
        elif stats.failures > stats.successes:
            failure_signal = (stats.failures - stats.successes) / outcome_count
            adjustment -= config.failure_penalty * failure_signal

    if stats.average_rating is not None:
        # Ratings are centered around 3.0: 1 is negative, 5 is positive.
        rating_signal = (stats.average_rating - 3.0) / 2.0
        if rating_signal > 0:
            adjustment += config.success_boost * rating_signal
        elif rating_signal < 0:
            adjustment += config.failure_penalty * rating_signal

    return round(clamp(adjustment, -config.max_adjustment, config.max_adjustment), 4)


def describe_adaptive_adjustment(
    stats: ModuleFeedbackStats | None,
    config: AdaptiveRoutingConfig,
    adjustment: float,
) -> str | None:
    """Create a human-readable explanation for an adaptive score adjustment."""
    if not config.enabled:
        return None
    if stats is None:
        return "adaptive routing enabled; no feedback history for this module"
    if stats.times_selected < config.min_feedback_records:
        return (
            "adaptive routing enabled; "
            f"only {stats.times_selected} feedback records, need {config.min_feedback_records}"
        )

    direction = "boost" if adjustment > 0 else "penalty" if adjustment < 0 else "neutral adjustment"
    details = [
        f"adaptive {direction} {adjustment:+.2f}",
        f"selected {stats.times_selected} times",
        f"successes {stats.successes}",
        f"failures {stats.failures}",
    ]
    if stats.average_rating is not None:
        details.append(f"average rating {stats.average_rating:.2f}")
    if stats.success_rate is not None:
        details.append(f"success rate {stats.success_rate:.2f}")
    return "; ".join(details)


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a value to an inclusive range."""
    return max(minimum, min(value, maximum))
