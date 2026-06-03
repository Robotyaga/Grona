"""Command-line helpers for the Grona routing prototype."""

from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Sequence

from .adaptive import AdaptiveRoutingConfig
from .context import ContextBuilder
from .decision import RoutingDecision
from .defaults import create_default_registry
from .feedback import FeedbackRecord, JsonlFeedbackStore
from .memory import create_default_memory_modules
from .orchestrator import OrchestrationResult, Orchestrator
from .router import Router

DEFAULT_TASK = "Analyze engine overheating symptoms and explain what to inspect first."


def format_decision(decision: RoutingDecision) -> str:
    """Format a routing decision for humans."""
    lines = [f"Task: {decision.task}"]
    if decision.adaptive_enabled:
        history_note = (
            "feedback history loaded" if decision.feedback_available else "no feedback history"
        )
        lines.extend(["", f"Adaptive routing: enabled ({history_note})"])
    lines.extend(["", "Selected modules:"])

    if decision.selected_modules:
        for match in decision.selected_modules:
            lines.append(f"- {match.module.name} (score {match.score:.1f})")
            if match.adaptive_enabled:
                lines.append(
                    f"  base score: {match.base_score:.1f}; "
                    f"adaptive adjustment: {match.adaptive_adjustment:+.2f}; "
                    f"final score: {match.final_score:.1f}"
                )
            for reason in match.reasons:
                lines.append(f"  reason: {reason}")
    else:
        lines.append("- none")

    lines.extend(["", "Skipped modules:"])
    if decision.skipped_modules:
        for match in decision.skipped_modules:
            lines.append(f"- {match.module.name} (score {match.score:.1f})")
            if match.adaptive_enabled:
                lines.append(
                    f"  base score: {match.base_score:.1f}; "
                    f"adaptive adjustment: {match.adaptive_adjustment:+.2f}; "
                    f"final score: {match.final_score:.1f}"
                )
            lines.append(f"  reason: {'; '.join(match.reasons)}")
    else:
        lines.append("- none")

    return "\n".join(lines)


def format_orchestration_result(result: OrchestrationResult) -> str:
    """Format an orchestration result for humans."""
    lines = [format_decision(result.routing_decision)]
    lines.extend(["", "Context items:"])
    if result.context_items:
        for item in result.context_items:
            kind = item.metadata.get("context_kind", "context")
            lines.append(f"- {item.source} ({kind}, relevance {item.relevance:.2f})")
            lines.append(f"  content: {item.content}")
            reasons = item.metadata.get("reasons")
            if reasons:
                lines.append(f"  reason: {'; '.join(str(reason) for reason in reasons)}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "Execution: not run; this prototype only prepares a structured handoff.",
            f"Orchestration summary: {result.summary}",
        ]
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Grona demo router from the command line."""
    parser = build_parser()
    args = parser.parse_args(argv)

    task = " ".join(args.task).strip() or DEFAULT_TASK
    feedback_file = args.feedback_file or args.save_feedback
    feedback_records = (
        load_feedback_records(feedback_file) if args.adaptive and feedback_file else ()
    )
    router = Router(
        create_default_registry(),
        top_k=args.top_k,
        adaptive_config=AdaptiveRoutingConfig(enabled=args.adaptive),
        feedback_records=feedback_records,
    )

    if args.orchestrate:
        context_builder = ContextBuilder(
            memory_modules=create_default_memory_modules() if args.use_demo_memory else (),
        )
        result = Orchestrator(router, context_builder=context_builder).run(task)
        print(format_orchestration_result(result))
        decision = result.routing_decision
    else:
        decision = router.route(task)
        print(format_decision(decision))

        print("\nActivated outputs:")
        for match, output in router.run(task):
            print(f"- {match.module.name}: {output}")
        if args.use_demo_memory:
            print("\nMemory note: --use-demo-memory is only used with --orchestrate.")

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
        "--adaptive",
        action="store_true",
        help="Enable feedback-informed score adjustments when feedback history is available.",
    )
    parser.add_argument(
        "--orchestrate",
        action="store_true",
        help="Build route-scoped context and prepare an orchestration handoff.",
    )
    parser.add_argument(
        "--use-demo-memory",
        action="store_true",
        help="Use built-in deterministic demo memory during orchestration.",
    )
    parser.add_argument(
        "--save-feedback",
        help="Optional JSONL file path for saving route feedback.",
    )
    parser.add_argument(
        "--feedback-file",
        help="Optional JSONL file path for loading adaptive history and saving route feedback.",
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


def load_feedback_records(feedback_file: str) -> tuple[FeedbackRecord, ...]:
    """Load feedback history for adaptive routing."""
    return JsonlFeedbackStore(feedback_file).list()


def parse_success(value: str | None) -> bool | None:
    """Parse an optional CLI success flag."""
    if value is None:
        return None
    return value == "true"
