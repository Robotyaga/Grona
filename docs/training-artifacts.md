# Training Artifact Bundle Foundation

The training artifact layer prepares deterministic, in-memory export bundles for future training experiments. It does not train a model, load a model, call an external API, download datasets, upload files, or write files by default.

This layer sits after `TrainingDatasetPackage` and `TrainingPlan`:

1. `TrainingDatasetPackage` owns reviewed examples, deterministic splits, and export manifests.
2. `TrainingPlan` owns config-only future adapter settings, validation, and card drafts.
3. `TrainingArtifactBuilder` turns both into a predictable `TrainingArtifactBundle`.
4. `TrainingArtifactWriter` can dry-run or explicitly write that bundle to a caller-provided directory.

## Public API

- `TrainingArtifact`: one text artifact with a safe relative path, content, content type, description, metadata, byte count, line count, and deterministic dictionary serialization.
- `TrainingArtifactBundle`: deterministic collection of artifacts with lookup, path listing, total byte count, and summary helpers.
- `TrainingArtifactBuilder`: builds the complete artifact bundle from a `TrainingDatasetPackage` and `TrainingPlan`.
- `TrainingArtifactWriteConfig`: conservative writer settings. Defaults are `dry_run=True`, `overwrite=False`, and `create_parents=False`.
- `TrainingArtifactWriter`: plans or writes bundle files only when the caller explicitly opts out of dry-run mode.
- `TrainingArtifactWriteReport`: records output directory, planned paths, written paths, skipped paths, errors, and count summary.

## Bundle Contents

`TrainingArtifactBuilder` creates these paths:

- `data/train.jsonl`
- `data/validation.jsonl`
- `data/test.jsonl`
- `config/training_config.json`
- `manifests/dataset_manifest.json`
- `manifests/training_export_manifest.json`
- `docs/dataset_card.md`
- `docs/model_card.md`
- `docs/safety_notes.md`
- `README.md`

Empty train, validation, or test splits still receive empty JSONL artifacts. The generated README calls out empty splits explicitly so callers can inspect the package without guessing whether a file was forgotten.

## Writer Safety

The writer is intentionally conservative:

- dry-run is the default
- an explicit `output_dir` is required by the caller
- parent directories are created only when `create_parents=True`
- existing files are not overwritten unless `overwrite=True`
- artifact paths are normalized as safe relative POSIX-style paths

A dry-run returns planned paths without touching the filesystem.

## CLI Demo

```bash
python -m grona --training-artifact-demo
```

The demo builds a tiny package and plan in memory, prints the artifact summary, shows README and training config previews, and does not write files.

To plan output paths without writing:

```bash
python -m grona --training-artifact-demo --artifact-output-dir ./training-artifacts
```

To write the demo bundle explicitly:

```bash
python -m grona --training-artifact-demo --artifact-output-dir ./training-artifacts --artifact-write
```

Use `--artifact-overwrite` only when replacing existing artifact files is intentional.

## Limitations

This is an export foundation, not a training system. It does not include training backends, model weights, tokenizer handling, dataset downloads, upload flows, LM Studio integration, external APIs, or production training claims.
