"""Console demo for human inference review policy checks."""

from __future__ import annotations

from collections.abc import Sequence
from json import dumps

from .inference_review import create_demo_inference_review_workflow


def format_inference_review_demo() -> str:
    """Return deterministic demo text for inference review workflows."""
    result = create_demo_inference_review_workflow()
    lines = [
        "Inference review demo",
        "Execution: deterministic offline review only; no LLMs, APIs, downloads, training, or databases.",
        "",
        "Reviews and policy decisions:",
    ]
    for index, (review, decision) in enumerate(
        zip(result.reviews, result.decisions, strict=True), start=1
    ):
        lines.extend(
            (
                f"[{index}] {review.review_id}",
                review.to_text(),
                decision.to_text(),
                "",
            )
        )
    lines.extend(
        (
            "Summary:",
            result.summary.to_text(),
            "",
            "JSON preview:",
            dumps(result.summary.to_dict(), sort_keys=True, indent=2),
        )
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Print the deterministic inference review demo."""
    _ = argv
    print(format_inference_review_demo())
    return 0
