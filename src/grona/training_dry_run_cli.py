"""CLI demo for the dry-run trainer interface foundation."""

from __future__ import annotations

from collections.abc import Sequence

from .training_dry_run import build_demo_training_execution_plan, command_preview_text


def main(argv: Sequence[str] | None = None) -> int:
    """Print the deterministic dry-run trainer demo."""
    _ = argv
    print(format_training_dry_run_demo())
    return 0


def format_training_dry_run_demo() -> str:
    """Return deterministic demo output for dry-run trainer planning."""
    execution_plan = build_demo_training_execution_plan()
    return "\n".join(
        (
            "Training dry-run trainer demo",
            "Execution: dry-run only; no model loading, no training, no files, no APIs.",
            "",
            "Readiness report:",
            execution_plan.readiness.to_text(),
            "",
            "Command preview:",
            command_preview_text(execution_plan.command_preview),
            "",
            "Warnings:",
            list_text(execution_plan.warnings),
            "",
            "Blockers:",
            list_text(execution_plan.blockers),
            "",
            "Execution plan JSON preview:",
            execution_plan.to_json(),
        )
    )


def list_text(values: tuple[str, ...]) -> str:
    """Return compact list lines with a none fallback."""
    if not values:
        return "- none"
    return "\n".join(f"- {value}" for value in values)
