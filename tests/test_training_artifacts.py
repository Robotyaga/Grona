from json import loads

from grona import (
    TrainingArtifact,
    TrainingArtifactBuilder,
    TrainingArtifactBundle,
    TrainingArtifactWriteConfig,
    TrainingArtifactWriter,
    TrainingSplitConfig,
    build_demo_training_plan,
    build_training_dataset_package,
)
from grona.entrypoint import main
from grona.training_artifacts import TRAINING_ARTIFACT_PATHS
from grona.training_plan import create_demo_training_plan_examples


def test_training_artifact_helpers_and_serialization() -> None:
    artifact = TrainingArtifact(
        "docs/example.md",
        "alpha\nbeta",
        "text/markdown",
        "Example artifact.",
        {"kind": "unit"},
    )

    data = artifact.to_dict()

    assert artifact.byte_count() == len("alpha\nbeta".encode("utf-8"))
    assert artifact.line_count() == 2
    assert data["path"] == "docs/example.md"
    assert data["metadata"] == {"kind": "unit"}


def test_training_artifact_rejects_unsafe_paths() -> None:
    for path in ("", "/tmp/example.md", "../example.md", "docs/../example.md"):
        try:
            TrainingArtifact(path, "content")
        except ValueError:
            continue
        raise AssertionError(f"unsafe artifact path was accepted: {path}")


def test_bundle_orders_artifacts_and_summarizes() -> None:
    bundle = TrainingArtifactBundle(
        "unit-bundle",
        (
            TrainingArtifact("z.txt", "z"),
            TrainingArtifact("a.txt", "alpha"),
        ),
    )

    assert bundle.artifact_paths() == ("a.txt", "z.txt")
    assert bundle.get_artifact("a.txt") is not None
    assert bundle.total_byte_count() == 6
    assert bundle.summary()["artifact_count"] == 2


def test_builder_produces_expected_artifact_paths() -> None:
    bundle = demo_bundle()

    assert set(bundle.artifact_paths()) == set(TRAINING_ARTIFACT_PATHS)
    assert bundle.artifact_paths() == tuple(sorted(TRAINING_ARTIFACT_PATHS))


def test_builder_includes_empty_split_jsonl_artifacts() -> None:
    package = build_training_dataset_package(
        create_demo_training_plan_examples()[:1],
        split_config=TrainingSplitConfig(),
        dataset_name="tiny-package",
        description="Tiny package for empty split artifact checks.",
    )
    plan = build_demo_training_plan(package)
    bundle = TrainingArtifactBuilder().build(package, plan)

    validation = bundle.get_artifact("data/validation.jsonl")
    test = bundle.get_artifact("data/test.jsonl")
    readme = bundle.get_artifact("README.md")

    assert validation is not None
    assert test is not None
    assert readme is not None
    assert validation.content == ""
    assert test.content == ""
    assert "is empty but still has an empty JSONL artifact" in readme.content


def test_training_config_and_manifests_are_valid_json() -> None:
    bundle = demo_bundle()

    for path in (
        "config/training_config.json",
        "manifests/dataset_manifest.json",
        "manifests/training_export_manifest.json",
    ):
        artifact = bundle.get_artifact(path)
        assert artifact is not None
        assert isinstance(loads(artifact.content), dict)


def test_dataset_and_model_cards_are_markdown() -> None:
    bundle = demo_bundle()

    dataset_card = bundle.get_artifact("docs/dataset_card.md")
    model_card = bundle.get_artifact("docs/model_card.md")
    safety_notes = bundle.get_artifact("docs/safety_notes.md")

    assert dataset_card is not None
    assert model_card is not None
    assert safety_notes is not None
    assert dataset_card.content.startswith("# Dataset Card Draft:")
    assert model_card.content.startswith("# Model Card Draft:")
    assert "not_trained_config_only" in model_card.content
    assert safety_notes.content.startswith("# Safety Notes")


def test_writer_dry_run_does_not_create_files(tmp_path) -> None:
    bundle = demo_bundle()
    output_dir = tmp_path / "artifact-output"

    report = TrainingArtifactWriter().write(bundle, output_dir)

    assert report.dry_run is True
    assert report.summary["planned"] == len(TRAINING_ARTIFACT_PATHS)
    assert report.summary["written"] == 0
    assert not output_dir.exists()


def test_writer_writes_only_when_enabled_with_parent_creation(tmp_path) -> None:
    bundle = demo_bundle()
    output_dir = tmp_path / "artifact-output"

    report = TrainingArtifactWriter().write(
        bundle,
        output_dir,
        TrainingArtifactWriteConfig(dry_run=False, create_parents=True),
    )

    assert report.summary["written"] == len(TRAINING_ARTIFACT_PATHS)
    assert report.summary["errors"] == 0
    assert (output_dir / "README.md").exists()
    assert (output_dir / "data" / "train.jsonl").exists()


def test_writer_refuses_overwrite_by_default(tmp_path) -> None:
    bundle = demo_bundle()
    output_dir = tmp_path / "artifact-output"
    writer = TrainingArtifactWriter()

    first = writer.write(
        bundle,
        output_dir,
        TrainingArtifactWriteConfig(dry_run=False, create_parents=True),
    )
    second = writer.write(
        bundle,
        output_dir,
        TrainingArtifactWriteConfig(dry_run=False, create_parents=True),
    )

    assert first.summary["written"] == len(TRAINING_ARTIFACT_PATHS)
    assert second.summary["written"] == 0
    assert second.summary["skipped"] == len(TRAINING_ARTIFACT_PATHS)
    assert second.summary["errors"] == len(TRAINING_ARTIFACT_PATHS)


def test_writer_requires_existing_output_dir_without_parent_creation(tmp_path) -> None:
    bundle = demo_bundle()
    output_dir = tmp_path / "missing-output"

    report = TrainingArtifactWriter().write(
        bundle,
        output_dir,
        TrainingArtifactWriteConfig(dry_run=False, create_parents=False),
    )

    assert report.summary["written"] == 0
    assert report.summary["skipped"] == len(TRAINING_ARTIFACT_PATHS)
    assert report.errors == ("output_dir does not exist and create_parents is false",)


def test_cli_training_artifact_demo_behavior(capsys) -> None:
    assert main(["--training-artifact-demo"]) == 0

    output = capsys.readouterr().out
    assert "Training artifact bundle demo" in output
    assert "no model loading, no training, no files, no APIs by default" in output
    assert "README preview" in output
    assert "Training config preview" in output
    assert "dry-run only" in output


def test_cli_training_artifact_write_requires_output_dir(capsys) -> None:
    assert main(["--training-artifact-demo", "--artifact-write"]) == 2

    output = capsys.readouterr().out
    assert "--artifact-write requires --artifact-output-dir" in output


def demo_bundle():
    package = build_training_dataset_package(
        create_demo_training_plan_examples(),
        split_config=TrainingSplitConfig(),
        dataset_name="unit-artifact-package",
        description="Unit test artifact package.",
    )
    plan = build_demo_training_plan(package)
    return TrainingArtifactBuilder().build(package, plan)
