"""Run a deterministic config-only training plan example."""

from grona import (
    AdapterTrainingSpec,
    BaseModelSpec,
    ModelCardDraft,
    TrainingRunConfig,
    TrainingRunValidator,
    TrainingSplitConfig,
    build_training_dataset_package,
)
from grona.training_plan import create_demo_training_plan_examples, dataset_summary_from_manifest


def main() -> None:
    """Print a deterministic fine-tuning plan scaffold without training."""
    package = build_training_dataset_package(
        create_demo_training_plan_examples(),
        split_config=TrainingSplitConfig(stratify_by_domain=True),
        dataset_name="example-training-plan-package",
        description="Reviewed examples for a config-only training plan example.",
    )
    base_model = BaseModelSpec(
        "Example local base model placeholder",
        "local-placeholder",
        "example/local-base-model",
        parameter_count="7B-placeholder",
        context_length=4096,
        license="demo-only",
        intended_use="future local adapter planning",
    )
    adapter = AdapterTrainingSpec(
        adapter_type="lora",
        rank=8,
        alpha=16,
        target_modules=("q_proj", "v_proj"),
    )
    config = TrainingRunConfig(
        "example-training-plan-config-only",
        base_model,
        adapter,
        package.manifest,
        dataset_summary_from_manifest(package.manifest),
        safety_notes=("No model is trained by this example.",),
    )
    validation = TrainingRunValidator().validate(config)
    card = ModelCardDraft(
        "Example adapter scaffold",
        base_model,
        adapter.adapter_type,
        dataset_summary_from_manifest(package.manifest),
        "Configuration review only.",
        ("No model has been trained.",),
        config.safety_notes,
        config.evaluation_plan,
    )

    print(config.to_text())
    print()
    print(validation.to_text())
    print()
    print(card.to_markdown())


if __name__ == "__main__":
    main()
