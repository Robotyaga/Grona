# Training Artifact Bundle Foundation

The training artifact layer prepares deterministic, in-memory export bundles for future training experiments. It does not train a model, load a model, call an external API, download datasets, upload files, or write files by default.

This layer sits after `TrainingDatasetPackage` and `TrainingPlan`:

1. `TrainingDatasetPackage` owns reviewed examples, deterministic splits, and export manifests.
2. `TrainingPlan` owns config-only future adapter settings, validation, and card drafts.
3. `TrainingArtifactBuilder` turns both into a predictable `TrainingArtifactBundle`.
4. `TrainingArtifactWriter` can dry-run or explicitly write that bundle to a caller-provided directory.
5. `DryRunTrainer` can inspect a bundle and return a dry-run [training execution plan](training-dry-run.md) without executing anything.
6. `TrainingBackendRegistry` can expose placeholder optional backends that declare required artifacts and dependency blockers.
7. `ExperimentalLoRABackend` can inspect the same bundle and build a guarded [LoRA job preview](experimental-lora-backend.md) without writing files or training.

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

## Dry-run Trainer Bridge

`TrainingArtifactBundle` can feed `DryRunTrainer`, which checks artifact readiness and produces a `TrainingExecutionPlan` with a placeholder command preview. That preview is never executed and is not a claim that training is implemented.

## Optional Backend Boundary Bridge

`TrainingArtifactBundle` can also feed a `PlaceholderTrainingBackend` from the [optional training backend boundary](training-backends.md). Placeholder backends declare which artifacts they require and return static dependency blockers for future LoRA or QLoRA integrations.

This keeps artifact packaging separate from future trainer execution. The boundary does not execute commands or import training packages.

## Experimental LoRA Bridge

`ExperimentalLoRABackend.prepare_training_job()` can inspect a `TrainingArtifactBundle` and produce a `LoRATrainingJob` preview. The preview maps expected train, validation, test, and config paths under an explicit output directory, but it does not write those paths and does not execute training.

This bridge uses the existing artifact bundle surface instead of creating a second parallel artifact format.

## CLI Demo

```bash
python -m grona --training-artifact-demo
python -m grona --training-backend-demo
python -m grona --experimental-lora-backend-demo
```

The artifact demo builds a tiny package and plan in memory, prints the artifact summary, shows README and training config previews, and does not write files.

The backend demo registers placeholder backends and previews readiness/dependency status for the same kind of artifact bundle.

The experimental LoRA demo builds a job preview from an in-memory artifact bundle and shows why execution remains blocked.

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

This is an export foundation, not a training system. It does not include executable training backends, model weights, tokenizer handling, dataset downloads, upload flows, LM Studio integration, external APIs, plugin auto-discovery, production training claims, or real LoRA training loops.
