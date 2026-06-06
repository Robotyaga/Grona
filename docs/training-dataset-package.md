# Training Dataset Package Foundation

The training dataset package layer turns already reviewed or validated `TrainingExample` candidates into deterministic in-memory train, validation, and test splits. It is a packaging and manifest foundation only.

It does not train a model, call an LLM, download datasets, upload data, write files by default, or claim that packaged examples are high-quality real training data.

## Main Records

- `TrainingSplitConfig` stores split ratios, random seed, optional simple domain stratification, and minimum split-size preferences.
- `TrainingDatasetSplitter` creates deterministic `train`, `validation`, and `test` splits from a `TrainingDataset` or a sequence of `TrainingExample` values.
- `TrainingDatasetSplit` stores one named split and summarizes counts, domains, sources, and validation statuses.
- `TrainingExportManifest` summarizes the full package: split counts, domains, capabilities, sources, licenses, validation statuses, provenance, warnings, and metadata.
- `TrainingDatasetPackage` keeps the original dataset, splits, and manifest together and can render native or Alpaca-like JSONL previews per split without writing files.
- `DatasetCardDraft` creates a Markdown draft that documents intended use, sources, licenses, validation process, limitations, splits, and warnings.

## Determinism

The splitter sorts examples by their existing `TrainingExample.sort_key()` before using a local `random.Random(seed)`. It does not touch global random state.

Default split config:

```python
TrainingSplitConfig(
    train_ratio=0.8,
    validation_ratio=0.1,
    test_ratio=0.1,
    seed=42,
    stratify_by_domain=False,
    min_examples_per_split=1,
)
```

For small datasets, the splitter keeps behavior practical and explicit. One or two examples stay in `train`; `validation` and `test` can be empty. The manifest warnings make underfilled splits visible instead of pretending that a tiny holdout is meaningful.

## Conservative Package Helper

Use `build_training_dataset_package()` for the common path:

```python
from grona import TrainingSplitConfig, build_training_dataset_package

package = build_training_dataset_package(
    examples,
    split_config=TrainingSplitConfig(seed=42, stratify_by_domain=True),
    dataset_name="reviewed-traces-v1",
    description="Reviewed trace candidates for future experiments.",
)

print(package.manifest.to_text())
print(package.native_jsonl_by_split()["train"])
```

The helper reuses `TrainingDataExporter` so raw and rejected records stay out by default. Warnings note skipped raw or rejected records and small split limitations.

## CLI Demo

```bash
python -m grona --training-package-demo
python examples/training_package_demo.py
```

The demo is deterministic and offline. It constructs tiny reviewed examples in memory, builds splits, prints a manifest, shows JSONL previews, and renders a dataset card draft.

## Boundaries

This layer is intentionally lightweight:

- no file writes by default
- no model calls
- no training
- no external APIs
- no dataset downloads
- no heavy dependencies
- no database or web server
- no quality guarantee

Callers that want durable artifacts should explicitly write the returned JSONL, manifest JSON, or dataset card text themselves.
