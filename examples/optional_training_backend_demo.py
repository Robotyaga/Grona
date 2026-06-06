"""Run the deterministic optional training plugin scaffold demo."""

from grona.training_dry_run import build_demo_training_dry_run_inputs, command_preview_text
from grona.training_plugins import (
    FutureLoRABackendStub,
    FutureQLoRABackendStub,
    build_optional_training_backend_design_report,
    create_optional_training_backend_registry,
    optional_training_dependency_specs,
)


if __name__ == "__main__":
    registry = create_optional_training_backend_registry()
    _package, plan, bundle = build_demo_training_dry_run_inputs()

    print("Optional dependency metadata:")
    for dependency in optional_training_dependency_specs():
        print(f"- {dependency.package}: {dependency.purpose}")

    print()
    print("Registered optional training backends:")
    for backend in registry.list_backends():
        print(f"- {backend.name}: {', '.join(backend.capabilities)}")

    lora_backend = registry.get("future-lora-backend-stub")
    qlora_backend = registry.get("future-qlora-backend-stub")
    assert isinstance(lora_backend, FutureLoRABackendStub)
    assert isinstance(qlora_backend, FutureQLoRABackendStub)

    print()
    print("LoRA dependency report:")
    print(lora_backend.check_dependencies().to_text())

    print()
    print("QLoRA dry-run plan is blocked because real training is not implemented:")
    execution_plan = qlora_backend.build_execution_plan(plan, bundle)
    print(execution_plan.readiness.to_text())
    print()
    print("Command preview, not executed:")
    print(command_preview_text(execution_plan.command_preview))

    print()
    print(build_optional_training_backend_design_report(registry).to_text())
