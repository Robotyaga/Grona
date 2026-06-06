"""Run the deterministic optional training backend boundary demo."""

from grona.training_backends import (
    TrainingBackendCapability,
    create_default_training_backend_registry,
)
from grona.training_dry_run import build_demo_training_dry_run_inputs, command_preview_text


if __name__ == "__main__":
    registry = create_default_training_backend_registry()
    package, plan, bundle = build_demo_training_dry_run_inputs()
    _ = package

    print("Registered training backends:")
    for backend in registry.list_backends():
        print(f"- {backend.name}: {', '.join(backend.capabilities)}")

    print()
    print("QLoRA-capable placeholders:")
    for backend in registry.find_by_adapter_type("qlora"):
        print(f"- {backend.name}")

    print()
    print("Command-preview-capable placeholders:")
    for backend in registry.find_by_capability(TrainingBackendCapability.COMMAND_PREVIEW):
        print(f"- {backend.name}")

    backend = registry.get("dry-run")
    execution_plan = backend.build_execution_plan(plan, bundle)
    print()
    print(execution_plan.readiness.to_text())
    print()
    print("Command preview:")
    print(command_preview_text(execution_plan.command_preview))
    print()
    print("Dependency report:")
    print(backend.check_dependencies().to_text())
