# Experimental LoRA Backend Skeleton

`ExperimentalLoRABackend` is a guarded implementation skeleton for a future LoRA training path. It is intentionally experimental and does not make Grona a production trainer.

It prepares structured metadata only:

- optional dependency availability report
- LoRA-shaped config compatibility checks
- artifact readiness report
- conservative safety report
- `LoRATrainingJob` preview

It does not train models, load models, load tokenizers, execute commands, spawn subprocesses, call shells, call external APIs, download models, download datasets, upload artifacts, write files, detect GPUs, or run an optimizer/scheduler/training loop.

## Why It Exists

Grona already has training export, dataset packaging, training plans, artifact bundles, dry-run trainer previews, placeholder backend contracts, and optional training plugin stubs. The experimental LoRA backend skeleton is the next narrow step: a real class at the backend boundary that can inspect config/artifacts and build a future job description while refusing execution by default.

This lets future real training work grow behind a controlled optional boundary instead of leaking heavy dependencies or execution behavior into Grona core.

## Core Records

`LoRATrainingJob` is a structured job description only. It includes:

- `job_id`
- `created_at`
- `run_name`
- `base_model`
- `adapter_config`
- `dataset_paths`
- `output_dir`
- `training_args`
- `warnings`
- `metadata`

It supports `to_dict()`, `to_json()`, and readable `to_text()` output.

`LoRATrainingSafetyConfig` is conservative by default:

- `allow_training_execution=False`
- `allow_model_download=False`
- `allow_dataset_download=False`
- `allow_overwrite_output=False`
- `require_explicit_confirmation=True`

`LoRATrainingReadinessReport` combines dependency, artifact, config, and safety reports with explicit warnings and blockers.

## Dependency Detection

Dependency detection uses `importlib.util.find_spec()` only. It checks package availability without importing heavy packages:

- `torch`
- `transformers`
- `peft`
- `accelerate`
- `datasets`
- optional `bitsandbytes`

There are no top-level imports of these packages. Normal Grona import, tests, examples, and CI do not require the ML stack.

Optional extras in `pyproject.toml` document future install surfaces:

```bash
pip install -e .[training]
pip install -e .[qlora]
```

CI does not install these extras.

## Demo

```bash
python -m grona --experimental-lora-backend-demo
python examples/experimental_lora_backend_demo.py
```

The demo builds a deterministic tiny training package, LoRA-shaped training plan, in-memory artifact bundle, dependency report, readiness report, and job preview. It also shows the guarded refusal path. It does not write files or execute training.

## Execution Guard

`run_training()` refuses by default. It requires:

- `allow_training_execution=True`
- an explicit confirmation token
- available required dependencies
- required artifacts

Even when these gates are passed, this PR still raises `NotImplementedError` because the real LoRA training loop is not implemented yet.

The confirmation token is intentionally loud:

```text
I_UNDERSTAND_GRONA_EXPERIMENTAL_LORA_TRAINING_IS_NOT_IMPLEMENTED
```

## Future Real LoRA Work

A future real LoRA implementation would still need:

- explicit dependency isolation
- real model/tokenizer loading policy
- local model path and download policy
- dataset path policy
- artifact output and overwrite policy
- hardware and CPU/GPU assumptions
- training loop implementation
- evaluation and rollback plan
- security review for file writes and execution
- CI strategy that does not require heavy ML packages by default

## Limitations

- no actual LoRA training
- no model loading
- no tokenizer loading
- no downloads
- no uploads
- no subprocess execution
- no shell execution
- no GPU detection
- no training loop
- no optimizer or scheduler implementation
- no real ML stack CI coverage
- no guarantee generated configs are correct for real models
- no production trainer
