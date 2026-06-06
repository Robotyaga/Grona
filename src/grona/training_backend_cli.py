"""CLI demo for optional training backend registration and placeholder planning."""

from __future__ import annotations

from collections.abc import Sequence

from .training_backends import (
    TrainingBackendCapability,
    create_default_training_backend_registry,
)
from .training_dry_run import build_demo_training_dry_run_inputs, command_preview_text


def main(argv: Sequence[str] | None = None) -> int:
    """Print the deterministic training backend boundary demo."""
    _ = argv
    print(format_training_backend_demo())
    return 0


def format_training_backend_demo() -> str:
    """Return deterministic demo output for optional training backends."""
    registry = create_default_training_backend_registry()
    _package, plan, bundle = build_demo_training_dry_run_inputs()
    selected = registry.get("dry-run")
    execution_plan = selected.build_execution_plan(plan, bundle)
    lora_backends = registry.find_by_adapter_type("lora")
    qlora_backends = registry.find_by_adapter_type("qlora")
    command_preview_backends = registry.find_by_capability(TrainingBackendCapability.COMMAND_PREVIEW)

    lines = [
        "Training backend boundary demo",
        "Execution: placeholder only; no training, no subprocesses, no shell, no APIs, no files.",
        "",
        "Registered backends:",
    ]
    for backend in registry.list_backends():
        dependency_report = backend.check_dependencies()
        lines.extend(
            (
                f"- {backend.name} ({backend.backend_type})",
                f"  capabilities: {', '.join(backend.capabilities) or 'none'}",
                f"  dependencies available: {dependency_report.available}",
                f"  missing: {', '.join(dependency_report.missing_dependencies) or 'none'}",
            )
        )
    lines.extend(
        (
            "",
            "Adapter lookup:",
            f"- lora: {', '.join(backend.name for backend in lora_backends) or 'none'}",
            f"- qlora: {', '.join(backend.name for backend in qlora_backends) or 'none'}",
            "",
            "Capability lookup:",
            f"- command_preview: {', '.join(backend.name for backend in command_preview_backends) or 'none'}",
            "",
            "Selected backend readiness:",
            execution_plan.readiness.to_text(),
            "",
            "Command preview:",
            command_preview_text(execution_plan.command_preview),
            "",
            "Dependency report:",
            selected.check_dependencies().to_text(),
            "",
            "Execution plan JSON preview:",
            execution_plan.to_json(),
        )
    )
    return "\n".join(lines)
