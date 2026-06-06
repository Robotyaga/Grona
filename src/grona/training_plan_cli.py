"""CLI demo for config-only fine-tuning training plans."""

from __future__ import annotations

from collections.abc import Sequence

from .training_plan import build_demo_training_plan


def main(argv: Sequence[str] | None = None) -> int:
    """Print the deterministic training plan scaffold demo."""
    _ = argv
    print(format_training_plan_demo())
    return 0


def format_training_plan_demo() -> str:
    """Return deterministic demo output for a config-only training plan."""
    plan = build_demo_training_plan()
    model_card = plan.model_card_draft.to_markdown() if plan.model_card_draft else "none"
    return "\n".join(
        (
            "Fine-tuning training plan demo",
            "Execution: config only; no model loading, no training, no files, no APIs.",
            "",
            plan.to_text(),
            "",
            "Warnings:",
            warnings_text(plan.validation.warnings),
            "",
            "Config JSON preview:",
            plan.config.to_json(),
            "",
            "Model card draft preview:",
            model_card,
        )
    )


def warnings_text(warnings: tuple[str, ...]) -> str:
    """Return compact warning lines."""
    if not warnings:
        return "none"
    return "\n".join(f"- {warning}" for warning in warnings)
