from json import loads

from grona import (
    AdapterTrainingSpec,
    BaseModelSpec,
    ModelCardDraft,
    TrainingRunConfig,
    TrainingRunValidator,
    TrainingSplitConfig,
    build_demo_training_plan,
    build_training_dataset_package,
)
from grona.entrypoint import main
from grona.training_plan import create_demo_training_plan_examples, dataset_summary_from_manifest


def test_base_model_spec_creation() -> None:
    spec = BaseModelSpec(
        "Demo base",
        "local",
        "demo/base",
        parameter_count="7B",
        context_length=4096,
        license="demo-only",
        intended_use="planning only",
    )

    assert spec.to_dict()["model_id"] == "demo/base"
    assert "Base model: Demo base" in spec.to_text()


def test_adapter_training_spec_creation() -> None:
    spec = AdapterTrainingSpec(
        adapter_type="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=("q_proj", "v_proj"),
    )

    assert spec.to_dict()["target_modules"] == ["q_proj", "v_proj"]
    assert "Adapter type: lora" in spec.to_text()


def test_training_run_config_json_and_dict() -> None:
    config = valid_config()

    data = config.to_dict()
    json_data = loads(config.to_json())

    assert data["run_name"] == "unit-test-plan"
    assert json_data["adapter"]["adapter_type"] == "lora"
    assert "Training run config: unit-test-plan" in config.to_text()


def test_training_run_validator_accepts_valid_config() -> None:
    result = TrainingRunValidator().validate(valid_config())

    assert result.valid is True
    assert result.errors == ()


def test_validator_rejects_missing_dataset_examples() -> None:
    package = build_training_dataset_package(
        (),
        dataset_name="empty",
        description="Empty package.",
    )
    config = valid_config(package=package)

    result = TrainingRunValidator().validate(config)

    assert result.valid is False
    assert "dataset must contain at least one train example" in result.errors
    assert "dataset manifest must contain at least one example" in result.errors


def test_validator_warns_on_tiny_dataset() -> None:
    package = build_training_dataset_package(
        create_demo_training_plan_examples()[:2],
        dataset_name="tiny",
        description="Tiny package.",
    )
    config = valid_config(package=package)

    result = TrainingRunValidator().validate(config)

    assert result.valid is True
    assert "dataset is tiny; this config is for scaffolding only" in result.warnings


def test_validator_rejects_invalid_lora_rank_and_alpha() -> None:
    adapter = AdapterTrainingSpec(adapter_type="lora", rank=0, alpha=0)
    config = valid_config(adapter=adapter)

    result = TrainingRunValidator().validate(config)

    assert result.valid is False
    assert "adapter rank must be positive" in result.errors
    assert "adapter alpha must be positive" in result.errors


def test_validator_rejects_missing_model_and_dataset_license_metadata() -> None:
    examples = tuple(
        example_with_license_unknown(index) for index in range(4)
    )
    package = build_training_dataset_package(
        examples,
        dataset_name="unknown-license",
        description="Unknown license package.",
    )
    base_model = BaseModelSpec("Demo base", "local", "demo/base", license="")
    config = valid_config(package=package, base_model=base_model)

    result = TrainingRunValidator().validate(config)

    assert result.valid is False
    assert "base model license must be present" in result.errors
    assert "dataset license summary must be present" in result.errors


def test_model_card_draft_markdown_output() -> None:
    config = valid_config()
    card = ModelCardDraft(
        "Unit model scaffold",
        config.base_model,
        config.adapter.adapter_type,
        config.dataset_package_summary,
        "planning only",
        ("No model has been trained.",),
        config.safety_notes,
        config.evaluation_plan,
    )

    markdown = card.to_markdown()

    assert markdown.startswith("# Model Card Draft: Unit model scaffold")
    assert "not_trained_config_only" in markdown
    assert "## Safety Notes" in markdown


def test_training_plan_creation() -> None:
    plan = build_demo_training_plan()

    assert plan.validation.valid is True
    assert plan.model_card_draft is not None
    assert "Training plan scaffold" in plan.to_text()
    assert plan.to_dict()["validation"]["valid"] is True


def test_demo_helper_deterministic_output() -> None:
    first = build_demo_training_plan()
    second = build_demo_training_plan()

    assert first.config.to_json() == second.config.to_json()
    assert first.model_card_draft is not None
    assert second.model_card_draft is not None
    assert first.model_card_draft.to_markdown() == second.model_card_draft.to_markdown()


def test_cli_training_plan_demo_behavior(capsys) -> None:
    assert main(["--training-plan-demo"]) == 0

    output = capsys.readouterr().out
    assert "Fine-tuning training plan demo" in output
    assert "config only" in output
    assert "not_trained_config_only" in output
    assert "Model card draft preview" in output


def valid_config(
    package=None,
    base_model: BaseModelSpec | None = None,
    adapter: AdapterTrainingSpec | None = None,
) -> TrainingRunConfig:
    dataset_package = package or build_training_dataset_package(
        create_demo_training_plan_examples(),
        split_config=TrainingSplitConfig(),
        dataset_name="unit-test-package",
        description="Unit test package.",
    )
    model = base_model or BaseModelSpec(
        "Unit base",
        "local",
        "unit/base",
        parameter_count="7B",
        context_length=4096,
        license="demo-only",
        intended_use="planning only",
    )
    spec = adapter or AdapterTrainingSpec(
        adapter_type="lora",
        rank=8,
        alpha=16,
        target_modules=("q_proj", "v_proj"),
    )
    return TrainingRunConfig(
        "unit-test-plan",
        model,
        spec,
        dataset_package.manifest,
        dataset_summary_from_manifest(dataset_package.manifest),
        epochs=1,
        learning_rate=0.0002,
        batch_size=1,
        gradient_accumulation_steps=4,
        max_sequence_length=2048,
        safety_notes=("Config-only validation; no training is performed.",),
    )


def example_with_license_unknown(index: int):
    example = create_demo_training_plan_examples()[index]
    return type(example)(
        instruction=example.instruction,
        input=example.input,
        output=example.output,
        source=example.source,
        domains=example.domains,
        capabilities=example.capabilities,
        provenance=example.provenance,
        license="unknown",
        validation_status=example.validation_status,
        metadata=example.metadata,
    )
