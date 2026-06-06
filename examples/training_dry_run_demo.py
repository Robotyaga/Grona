"""Run the deterministic dry-run trainer interface demo."""

from grona.training_dry_run import (
    DryRunTrainer,
    DryRunTrainerConfig,
    TrainingArtifactBuilder,
    build_demo_training_dry_run_inputs,
    command_preview_text,
    create_dry_run_backend_spec,
)


if __name__ == "__main__":
    package, plan, _bundle = build_demo_training_dry_run_inputs()
    bundle = TrainingArtifactBuilder().build(package, plan, name="example-training-dry-run-bundle")
    execution_plan = DryRunTrainer().create_execution_plan(
        plan,
        bundle,
        create_dry_run_backend_spec(),
        DryRunTrainerConfig(backend_name="dry-run"),
    )

    print(execution_plan.readiness.to_text())
    print()
    print("Command preview:")
    print(command_preview_text(execution_plan.command_preview))
