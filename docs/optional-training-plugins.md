# Optional Real-training Plugin Scaffold

The optional training plugin scaffold prepares a safe surface for future real LoRA or QLoRA training integrations without adding training execution to Grona core.

It does not train models, load models, execute commands, spawn subprocesses, call shells, call LM Studio, call external APIs, download models, download datasets, upload artifacts, write files by default, probe hardware, or import heavy ML packages.

## Why This Is Optional

Grona core should remain deterministic, offline, and dependency-light. Real training would require heavy packages, hardware assumptions, model licensing, dataset review, artifact policy, and evaluation policy. Those concerns should live behind explicit optional backends, not inside the core package.

This scaffold documents what future plugins would need while keeping today’s package safe.

## Main Records

`OptionalDependencySpec` describes a future dependency as metadata only:

- name
- package
- purpose
- required backend types
- install hint
- required flag
- metadata

Example metadata includes `torch`, `transformers`, `peft`, `accelerate`, `bitsandbytes`, and `datasets`. These packages are not added to `pyproject.toml` dependencies and are not imported.

`OptionalTrainingDependencyReport` reports whether optional training dependencies are available. In this scaffold, reports are metadata-only and blocked by default. They do not import packages or inspect the local machine.

`FutureLoRABackendStub` declares a future LoRA backend shape. It supports LoRA metadata, required artifacts, optional dependencies, and blocked dry-run readiness. It refuses real execution.

`FutureQLoRABackendStub` declares a future QLoRA backend shape. It declares planned quantization capability and QLoRA dependencies, including `bitsandbytes` metadata, but does not import or use them.

`TrainingBackendDesignReport` summarizes registered backends, future stubs, optional dependencies, missing capabilities, limitations, and next implementation steps.

## Registry Helper

`create_optional_training_backend_registry()` returns a deterministic registry with:

- `dry-run`
- `future-lora-backend-stub`
- `future-qlora-backend-stub`

The registry is explicit. There is no plugin auto-discovery from installed packages.

## CLI Demo

```bash
python -m grona --optional-training-backend-demo
python examples/optional_training_backend_demo.py
```

The demo prints backend stubs, dependency metadata, static dependency reports, a blocked dry-run plan, and a design report. It does not train, import heavy packages, write files, or access the network.

## Future Real-training PR Requirements

A future real-training PR would need to:

- add a separate optional package or plugin, not core dependencies
- define explicit dependency probing behind caller opt-in
- define a real execution contract separate from dry-run planning
- validate model and dataset licenses
- define artifact output policy
- define evaluation and rollback policy
- preserve source provenance
- keep training disabled by default
- document CPU/GPU assumptions honestly

## Limitations

- no real LoRA training
- no real QLoRA training
- no `torch`, `transformers`, `peft`, `bitsandbytes`, `datasets`, or `accelerate` dependency
- no heavy package imports
- no model loading
- no tokenizer loading
- no model downloads
- no dataset downloads
- no subprocess execution
- no shell execution
- no hardware probing
- no artifact upload
- no file writes by default
- no plugin auto-discovery from installed packages
- no guarantee future commands are correct
- no production trainer
