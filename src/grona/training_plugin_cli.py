"""CLI demo for optional real-training plugin scaffolding."""

from __future__ import annotations

from collections.abc import Sequence

from .training_dry_run import build_demo_training_dry_run_inputs, command_preview_text
from .training_plugins import (
    FutureLoRABackendStub,
    FutureQLoRABackendStub,
    build_optional_training_backend_design_report,
    create_optional_training_backend_registry,
    optional_training_dependency_specs,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Print the deterministic optional training plugin scaffold demo."""
    _ = argv
    print(format_optional_training_backend_demo())
    return 0


def format_optional_training_backend_demo() -> str:
    """Return deterministic demo output for optional real-training stubs."""
    registry = create_optional_training_backend_registry()
    _package, plan, bundle = build_demo_training_dry_run_inputs()
    lora_backend = registry.get("future-lora-backend-stub")
    qlora_backend = registry.get("future-qlora-backend-stub")
    qlora_plan = qlora_backend.build_execution_plan(plan, bundle)
    design_report = build_optional_training_backend_design_report(registry)

    lines = [
        "Optional training backend plugin scaffold demo",
        "Execution: metadata and dry-run only; real training is not implemented.",
        "No model loading, no subprocesses, no shell, no APIs, no files, no heavy imports.",
        "",
        "Registered optional training backends:",
    ]
    for backend in registry.list_backends():
        lines.extend(
            (
                f"- {backend.name} ({backend.backend_type})",
                f"  capabilities: {', '.join(backend.capabilities) or 'none'}",
                f"  required dependencies: {', '.join(backend.required_dependencies) or 'none'}",
            )
        )
    lines.extend(
        (
            "",
            "Future dependency metadata:",
        )
    )
    for dependency in optional_training_dependency_specs():
        lines.append(f"- {dependency.package}: {dependency.purpose}")
    lines.extend(
        (
            "",
            "LoRA stub dependency report:",
            lora_backend.check_dependencies().to_text(),
            "",
            "QLoRA stub dependency report:",
            qlora_backend.check_dependencies().to_text(),
            "",
            "QLoRA blocked dry-run execution plan:",
            qlora_plan.readiness.to_text(),
            "",
            "Command preview is not executed:",
            command_preview_text(qlora_plan.command_preview),
            "",
            "Design report:",
            design_report.to_text(),
            "",
            "Real training status:",
            "not installed, not implemented, not executed",
        )
    )
    assert isinstance(lora_backend, FutureLoRABackendStub)
    assert isinstance(qlora_backend, FutureQLoRABackendStub)
    return "\n".join(lines)
