from json import loads

from grona import (
    DatasetCardDraft,
    TrainingDataset,
    TrainingDatasetPackage,
    TrainingDatasetSplit,
    TrainingDatasetSplitter,
    TrainingExportManifest,
    TrainingExample,
    TrainingSplitConfig,
    build_training_dataset_package,
)
from grona.entrypoint import main


def test_training_split_config_defaults() -> None:
    config = TrainingSplitConfig()

    assert config.train_ratio == 0.8
    assert config.validation_ratio == 0.1
    assert config.test_ratio == 0.1
    assert config.seed == 42
    assert config.normalized_ratios() == (0.8, 0.1, 0.1)
    assert loads(config.to_json())["seed"] == 42


def test_training_dataset_split_summaries() -> None:
    split = TrainingDatasetSplit("train", demo_examples(3))

    assert split.count() == 3
    assert split.domains() == ("documents", "routing", "safety")
    assert split.sources() == ("reviewed_inference_trace",)
    assert split.validation_status_counts() == {"reviewed": 3}
    assert "Split: train" in split.to_text()


def test_deterministic_split_output() -> None:
    examples = demo_examples(12)
    splitter = TrainingDatasetSplitter(TrainingSplitConfig(seed=123))

    first = splitter.split(examples)
    second = splitter.split(tuple(reversed(examples)))

    assert split_outputs(first) == split_outputs(second)


def test_medium_dataset_ratios() -> None:
    splits = TrainingDatasetSplitter().split(demo_examples(10))

    assert [split.count() for split in splits] == [8, 1, 1]


def test_small_dataset_behavior_keeps_train_populated() -> None:
    splits = TrainingDatasetSplitter().split(demo_examples(2))

    assert [split.count() for split in splits] == [2, 0, 0]


def test_stratified_split_is_deterministic_and_populates_training_domains() -> None:
    config = TrainingSplitConfig(seed=77, stratify_by_domain=True)
    splits = TrainingDatasetSplitter(config).split(demo_examples(12))

    assert split_outputs(splits) == split_outputs(TrainingDatasetSplitter(config).split(demo_examples(12)))
    assert set(splits[0].domains()) == {"documents", "routing", "safety"}


def test_manifest_summaries_and_json_roundtrip() -> None:
    dataset = TrainingDataset("demo", "Demo dataset.", demo_examples(6))
    config = TrainingSplitConfig(seed=5)
    splits = TrainingDatasetSplitter(config).split(dataset)
    manifest = TrainingExportManifest.from_dataset_and_splits(dataset, splits, config)

    rebuilt = TrainingExportManifest.from_json(manifest.to_json())

    assert manifest.total_examples == 6
    assert manifest.domain_summary == {"documents": 2, "routing": 2, "safety": 2}
    assert manifest.source_summary == {"reviewed_inference_trace": 6}
    assert manifest.provenance_summary["trace_count"] == 6
    assert rebuilt.to_dict() == manifest.to_dict()


def test_training_dataset_package_previews() -> None:
    package = build_training_dataset_package(
        demo_examples(6),
        dataset_name="package-demo",
        description="Package demo.",
    )

    native = package.native_jsonl_by_split()
    alpaca = package.alpaca_jsonl_by_split()

    assert isinstance(package, TrainingDatasetPackage)
    assert set(native) == {"train", "validation", "test"}
    assert "validation_status" in native["train"]
    assert set(loads(alpaca["train"].splitlines()[0])) == {"instruction", "input", "output"}
    assert "Training export manifest: package-demo" in package.to_text()


def test_dataset_card_markdown() -> None:
    package = build_training_dataset_package(
        demo_examples(4),
        dataset_name="card-demo",
        description="Card demo.",
    )
    card = DatasetCardDraft.from_package(package)

    markdown = card.to_markdown()

    assert markdown.startswith("# Dataset Card Draft: card-demo")
    assert "## Splits" in markdown
    assert "- train:" in markdown
    assert "## Limitations" in markdown


def test_package_helper_filters_raw_and_is_deterministic() -> None:
    examples = (*demo_examples(5), demo_example(99, status="raw"))

    first = build_training_dataset_package(examples, dataset_name="demo", description="Demo.")
    second = build_training_dataset_package(tuple(reversed(examples)), dataset_name="demo", description="Demo.")

    assert first.dataset.count() == 5
    assert first.manifest.to_json() == second.manifest.to_json()
    assert first.native_jsonl_by_split() == second.native_jsonl_by_split()
    assert first.manifest.warnings == ("1 raw examples will be skipped by export policy.",)


def test_cli_training_package_demo_behavior(capsys) -> None:
    assert main(["--training-package-demo"]) == 0

    output = capsys.readouterr().out
    assert "Training dataset package demo" in output
    assert "deterministic offline package only" in output
    assert "Training export manifest" in output
    assert "Dataset card draft preview" in output


def split_outputs(splits: tuple[TrainingDatasetSplit, ...]) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(example.instruction for example in split.examples) for split in splits)


def demo_examples(count: int) -> tuple[TrainingExample, ...]:
    return tuple(demo_example(index) for index in range(count))


def demo_example(index: int, status: str = "reviewed") -> TrainingExample:
    domains = ("routing", "documents", "safety")
    capabilities = ("route_trace", "context_review", "safety_review")
    domain = domains[index % len(domains)]
    capability = capabilities[index % len(capabilities)]
    return TrainingExample(
        instruction=f"Instruction {index:02d}",
        input=f"Input {index}",
        output=f"Output {index}",
        source="reviewed_inference_trace",
        domains=(domain,),
        capabilities=(capability,),
        provenance={
            "origin": "reviewed_inference_trace",
            "trace_id": f"trace:{index:02d}",
            "review_id": f"review:{index:02d}",
        },
        license="demo-only",
        validation_status=status,
        metadata={"index": index},
    )
