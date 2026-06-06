# Local Training Handoff

This document describes how to move Grona from GitHub/Codex repository construction into local development in a tool such as Google Antigravity or another local IDE.

The repository is ready for local handoff. It is not ready for real model training.

## Local Setup

Clone the repository locally, then install the lightweight development dependencies:

```bash
pip install -e .[dev]
```

Run the safe checks:

```bash
pytest
ruff check .
```

The core package has no mandatory runtime dependencies and should remain lightweight.

## Safe Demos

The following demos are safe planning and inspection flows:

```bash
python -m grona --model-build-readiness-demo
python -m grona --training-pipeline-audit-demo
python -m grona --experimental-lora-backend-demo
python -m grona --training-artifact-demo
```

These commands do not train models, load models, call external APIs, download datasets, download model weights, upload files, or execute training subprocesses.

## Dry-Run First

Before any future real training backend is implemented locally, inspect the deterministic training pipeline:

1. Build reviewed trace training examples.
2. Build a `TrainingDatasetPackage`.
3. Build a `TrainingArtifactBundle` in memory.
4. Inspect `TrainingPlan` validation.
5. Run the dry-run trainer readiness checks.
6. Run `--training-pipeline-audit-demo`.
7. Run `--model-build-readiness-demo`.

Artifact writing must remain explicit. Do not add file writes as hidden side effects.

## Optional Future Dependencies

Future local LoRA or QLoRA experiments may require optional packages such as:

- `torch`
- `transformers`
- `peft`
- `accelerate`
- `datasets`
- `bitsandbytes`

These are optional and future-only. They are not installed in CI, not required for normal imports, and not required for current tests.

## What Is Still Blocked

The following operations must not happen accidentally:

- real model training
- model loading
- shell or subprocess execution
- external API calls
- model or dataset downloads
- artifact uploads
- file writes by default

Any future trainer must require explicit safety configuration, explicit local dependency setup, explicit artifact/output policy, and explicit confirmation that the user understands the experimental state.

## Recommended Local IDE Path

When moving to Google Antigravity or another local IDE:

1. Keep the current tests green before adding trainer code.
2. Start with environment profile modeling, not execution.
3. Add local-only dependency checks without importing heavy packages at top level.
4. Keep real training behind explicit safety gates.
5. Add tests around every new boundary before allowing any execution path.
6. Keep CI free of heavy ML dependencies.

The next practical implementation step is still not real training. It is a local-only trainer design spike that proves dependency isolation, output policy, and safety gates before any model is loaded.
