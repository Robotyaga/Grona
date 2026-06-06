# Optional Training Backend Boundary

The training backend boundary defines how future real training integrations should declare themselves before Grona adds any executable trainer.

It is intentionally lightweight and core-safe. It does not train models, execute commands, spawn subprocesses, call shells, call LM Studio, call external APIs, download models, download datasets, upload artifacts, write files by default, probe GPUs, or import heavy ML packages.

## Why Backends Are Optional

Grona core should stay deterministic, offline, and dependency-light. Real LoRA or QLoRA training would require separate review of hardware assumptions, model licenses, dataset quality, evaluation policy, artifact policy, and safety boundaries.

The backend boundary makes future integration points explicit without adding `torch`, `transformers`, `peft`, `bitsandbytes`, `datasets`, `accelerate`, or similar packages to the core package.

## Main API

`TrainingBackend` is a protocol for future optional backends. A backend declares:

- `name`
- `backend_type`
- `capabilities`
- `required_artifacts`
- `required_dependencies`
- `supports(config)`
- `check_readiness(training_plan, artifact_bundle, config)`
- `build_execution_plan(training_plan, artifact_bundle, config)`
- `check_dependencies()`

The protocol is a contract only. It does not require or import training dependencies.

`TrainingBackendCapability` provides stable capability labels such as:

- `lora`
- `qlora`
- `full_finetune`
- `dry_run`
- `command_preview`
- `quantization`
- `gpu_required`
- `cpu_possible`

`TrainingBackendRegistry` supports explicit backend registration, deterministic listing, lookup by name, lookup by adapter type, and lookup by capability.

`TrainingBackendDependencyReport` records static dependency status:

- backend name
- available flag
- missing dependencies
- optional dependencies
- warnings
- blockers
- metadata

Dependency reports are static in this foundation. They do not import heavy packages or inspect the local environment.

`TrainingBackendMetadata` documents optional backend packaging information, supported adapter types, supported quantization labels, supported artifact formats, install hints, and limitations.

## Placeholder Backends

`PlaceholderTrainingBackend` implements the protocol safely. It wraps existing dry-run trainer planning and returns a `TrainingExecutionPlan` without execution.

The default registry includes:

- `dry-run`
- `lora-cli-placeholder`
- `qlora-cli-placeholder`

The LoRA and QLoRA placeholders list future package names only as descriptive dependency requirements. They are not installed, imported, or executed. Their dependency reports are blocked by default so the project cannot accidentally imply that real training is ready.

## CLI Demo

```bash
python -m grona --training-backend-demo
python examples/training_backend_demo.py
```

The demo creates a registry, registers placeholder backends, prints capabilities, prints static dependency reports, performs adapter/capability lookup, and builds a dry-run execution plan through the `dry-run` placeholder backend.

## Future Plugin Direction

Future real training should live behind explicit optional packages or plugins. A future backend should:

- declare capabilities before use
- declare required artifacts and dependencies
- refuse unsupported adapter configs
- report missing dependencies before execution
- return dry-run execution plans for review
- keep actual execution behind a separate explicit opt-in design

Grona core should not silently discover or execute trainer plugins. Any future auto-discovery should be metadata-only until reviewed.

## Limitations

- no actual training
- no executable trainer backend
- no subprocess or shell execution
- no package imports for dependency checks
- no `torch`, `transformers`, `peft`, `bitsandbytes`, `datasets`, or `accelerate`
- no model loading or tokenizer loading
- no model downloads
- no dataset downloads
- no artifact uploads
- no file writes by default
- no plugin auto-discovery
- no GPU or hardware probing
- no guarantee future command previews are runnable
- no production trainer
