"""Run the deterministic model-build readiness demo without training anything."""

from grona import (
    ExperimentalLoRABackend,
    LoRATrainingSafetyConfig,
    ModelBuildReadinessAuditor,
    TrainingEnvironmentAuditor,
    TrainingHardwareRequirement,
    build_model_build_demo_pipeline_inputs,
    create_cpu_only_demo_environment,
    create_missing_dependencies_demo_environment,
    model_build_lifecycle_markdown,
)


def main() -> None:
    """Print a local handoff readiness report without loading or training models."""
    examples, package, plan, bundle = build_model_build_demo_pipeline_inputs()
    backend = ExperimentalLoRABackend(dependency_finder=lambda _package: None)
    environment = create_cpu_only_demo_environment()
    report = ModelBuildReadinessAuditor().audit(
        examples=examples,
        package=package,
        training_plan=plan,
        artifact_bundle=bundle,
        backend=backend,
        environment_profile=environment,
        environment_requirement=TrainingHardwareRequirement.cpu_dry_run(),
        safety_config=LoRATrainingSafetyConfig(),
    )
    qlora_report = TrainingEnvironmentAuditor().audit(
        create_missing_dependencies_demo_environment(),
        TrainingHardwareRequirement.small_qlora(),
    )

    print(report.to_text())
    print()
    print("Local handoff manifest:")
    print(report.handoff_manifest.to_markdown())
    print()
    print("QLoRA environment example:")
    print(qlora_report.to_text())
    print()
    print(model_build_lifecycle_markdown())


if __name__ == "__main__":
    main()
