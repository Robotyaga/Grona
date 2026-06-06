# Dry-run Trainer Interface Foundation

The dry-run trainer layer validates a future training run and builds a deterministic execution preview without training anything.

It sits after the existing training preparation layers:

1. `TrainingDataExporter` creates explicit reviewed training example candidates.
2. `TrainingDatasetPackage` creates deterministic train, validation, and test splits.
3. `TrainingPlan` creates a config-only future adapter plan.
4. `TrainingArtifactBuilder` creates an in-memory artifact bundle.
5. `DryRunTrainer` validates readiness and returns a `TrainingExecutionPlan`.
6. `TrainingBackendRegistry` can expose placeholder optional backend boundaries that reuse this dry-run planning layer.

This layer is intentionally not a trainer. It does not execute commands, spawn subprocesses, call shells, load models, call LM Studio, call external APIs, download datasets, upload artifacts, or write files by default.

## Main Records

`TrainerBackendSpec` describes a possible future backend:

- name
- backend type
- description
- required commands
- required Python packages
- supported adapter types
- quantization support
- metadata

The spec is descriptive only. It does not probe the local machine, import packages, or verify command availability.

`DryRunTrainerConfig` controls conservative readiness checks:

- require training plan validation to pass
- require a non-empty train split
- require base model license metadata
- require dataset manifest artifact
- optionally allow missing optional artifacts

`TrainingReadinessReport` records whether the dry-run is ready, warnings, blockers, artifact counts, required artifact status, config validation status, and train example count.

`TrainingExecutionPlan` combines the training config, artifact bundle summary, backend spec, readiness report, environment notes, warnings, blockers, and command preview.

## Backend Presets

The foundation includes deterministic preset helpers:

- `create_dry_run_backend_spec()`
- `create_lora_cli_placeholder_backend_spec()`
- `create_qlora_cli_placeholder_backend_spec()`

These are still specifications, not real backends. The LoRA and QLoRA presets list future package names such as `torch`, `transformers`, `peft`, or `bitsandbytes` only as descriptive requirements. Grona does not add or import those dependencies.

## Optional Backend Boundary

The [optional training backend boundary](training-backends.md) wraps these specs in explicit placeholder backends and a deterministic registry. That layer answers which future backend capabilities exist, which dependencies would be required, and whether a backend can build a dry-run plan.

It still does not execute commands or train models. LoRA and QLoRA placeholder backends report missing optional dependencies by default instead of pretending real training is available.

## Command Preview

The command preview is a placeholder argument list. Example:

```text
python -m grona_train_placeholder --backend dry-run --config config/training_config.json --train data/train.jsonl --validation data/validation.jsonl --test data/test.jsonl --output-dir outputs/demo-training-plan-config-only --dry-run-placeholder-not-implemented
```

This command is not executed. Grona does not add a real `grona_train_placeholder` trainer in this layer. The preview exists so reviewers can inspect which artifacts a future explicit training runner would consume.

## Readiness Checks

`DryRunTrainer` checks the in-memory training plan and artifact bundle for:

- required artifact paths
- training config validation result
- non-empty train split
- base model license metadata
- backend adapter support
- backend quantization support

Missing required artifacts, invalid config, empty train split, missing model license, unsupported adapter type, or unsupported quantization become blockers.

Warnings remain visible but do not block unless the configured check requires them to.

## CLI Demo

```bash
python -m grona --training-dry-run-demo
python -m grona --training-backend-demo
python examples/training_dry_run_demo.py
python examples/training_backend_demo.py
```

The dry-run demo creates deterministic reviewed examples, builds a dataset package, builds a training plan, builds an artifact bundle, creates a dry-run backend spec, runs `DryRunTrainer`, and prints readiness plus command preview.

The backend demo creates a registry and shows placeholder backend capability/dependency reports before building a dry-run execution plan.

## Limitations

- no actual training
- no subprocess execution
- no shell command execution
- no `torch`
- no `transformers`
- no `peft`
- no `bitsandbytes`
- no `datasets`
- no `accelerate`
- no model loading
- no model downloads
- no dataset downloads
- no dataset or model uploads
- no GPU or hardware detection
- no environment probing by default
- no plugin auto-discovery
- no guarantee that the command preview is directly runnable
- no production trainer yet

Future real training work should be added as a separate explicit backend only after artifact policy, evaluation policy, hardware assumptions, data review, and safety boundaries are reviewed.
