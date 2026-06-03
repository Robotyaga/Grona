"""Demonstrate feedback-informed adaptive routing in Grona."""

from grona import (
    AdaptiveRoutingConfig,
    FeedbackRecord,
    Router,
    create_default_registry,
)
from grona.cli import format_decision

TASK = "Review this Python script for security issues and suspicious network behavior."


def main() -> None:
    registry = create_default_registry()
    base_router = Router(registry, top_k=3)
    base_decision = base_router.route(TASK)

    print("Before feedback")
    print(format_decision(base_decision))

    positive_feedback = [
        FeedbackRecord.from_decision(base_decision, success=True, rating=5),
        FeedbackRecord.from_decision(base_decision, success=True, rating=5),
    ]
    positive_router = Router(
        registry,
        top_k=3,
        adaptive_config=AdaptiveRoutingConfig(enabled=True),
        feedback_records=positive_feedback,
    )
    print("\nAfter positive feedback")
    print(format_decision(positive_router.route(TASK)))

    negative_feedback = [
        FeedbackRecord.from_decision(base_decision, success=False, rating=1),
        FeedbackRecord.from_decision(base_decision, success=False, rating=2),
    ]
    negative_router = Router(
        registry,
        top_k=3,
        adaptive_config=AdaptiveRoutingConfig(enabled=True),
        feedback_records=negative_feedback,
    )
    print("\nAfter negative feedback")
    print(format_decision(negative_router.route(TASK)))


if __name__ == "__main__":
    main()
