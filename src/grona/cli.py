"""Command-line helpers for the Grona routing prototype."""

from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Sequence

from .decision import RoutingDecision
from .defaults import create_default_registry
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
    parser = ArgumentParser(description="Route a task through Grona's demo module registry.")
    parser.add_argument("task", nargs="*", help="Task text to route. Uses a demo task if omitted.")
    parser.add_argument("--top-k", type=int, default=3, help="Maximum number of modules to select.")
    args = parser.parse_args(argv)

    task = " ".join(args.task).strip() or DEFAULT_TASK
    router = Router(create_default_registry(), top_k=args.top_k)
    decision = router.route(task)
    print(format_decision(decision))

    print("\nActivated outputs:")
    for match, output in router.run(task):
        print(f"- {match.module.name}: {output}")
    return 0
