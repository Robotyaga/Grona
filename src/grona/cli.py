"""Command-line helpers for the Grona routing prototype."""

from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Sequence

from .decision import RoutingDecision
from .defaults import create_default_registry
from .feedback import FeedbackRecord, JsonlFeedbackStore
from .router import Router

DEFAULT_TASK = "Analyze engine overheating symptoms and explain what to inspect first."


def format_decision(decision: RoutingDecision) -> str:
    """Format a routing decision for humans."""
    lines = [f"Task: {decision.task}", "", "Selected modules:"]
    if decision.selected_modules:
        for match in decision.selected_modules:
            lines.append(f"- {match.module.name} (score {match.score:.1f})")
            for reason in match.reasons:
                lines.append(f"  reason: {reason}")
    else:
        lines.append("- none")

    lines.extend(["", "Skipped modules:"])
    if decision.skipped_modules:
        for match in decision.skipped_modules:
            lines.append(f"- {match.module.name} (score {match.score:.1f})")
            lines.append(f"  reason: {'; '.join(match.reasons)}")
    else:
        lines.append("- none")

    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Grona demo router from the command line."""
    parser = build_parser()
    args = parser.parse_args(argv)

    task = " ".join(args.task).strip() or DEFAULT_TASK
    router = Router(create_default_registry(), top_k=args.top_k)
    decision = router.route(task)
    print(format_decision(decision))

    print("\nActivated outputs:")
    for match, output in router.run(task):
        print(f"- {match.module.name}: {output}")

    feedback_file = args.feedback_file or args.save_feedback
    if feedback_file:
        record = FeedbackRecord.from_decision(
            decision,
            rating=args.rating,
            success=parse_success(args.success),
            notes=args.notes,
        )
        JsonlFeedbackStore(feedback_file).add(record)
        print(f"\nSaved feedback: {feedback_file}")

    return 0


def build_parser() -> ArgumentParser:
    """Build the CLI argument parser."""
    parser = ArgumentParser(description="Route a task through Grona's demo module registry.")
    parser.add_argument("task", nargs="*", help="Task text to route. Uses a demo task if omitted.")
    parser.add_argument("--top-k", type=int, default=3, help="Maximum number of modules to select.")
    parser.add_argument(
        "--save-feedback",
        help="Optional JSONL file path for saving route feedback.",
    )
    parser.add_argument(
        "--feedback-file",
        help="Optional JSONL file path for saving route feedback.",
    )
    parser.add_argument(
        "--rating",
        type=int,
        choices=range(1, 6),
        help="Optional route rating, 1-5.",
    )
    parser.add_argument(
        "--success",
        choices=("true", "false"),
        help="Optional route outcome flag.",
    )
    parser.add_argument("--notes", help="Optional route outcome notes.")
    return parser


def parse_success(value: str | None) -> bool | None:
    """Parse an optional CLI success flag."""
    if value is None:
        return None
    return value == "true"
