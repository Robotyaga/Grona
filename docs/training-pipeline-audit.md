# Training Pipeline Readiness Audit

The training pipeline readiness audit hardens Grona's training-preparation contracts before any real LoRA or QLoRA training backend is added.

It does not train models, load models, execute commands, spawn subprocesses, call shells, call external APIs, download models, download datasets, upload artifacts, write files by default, probe GPUs, or import heavy ML packages.

For the final local-development handoff layer that combines this audit with explicit environment readiness, backend readiness, artifact summaries, and a local IDE checklist, see [Model build readiness](model-build-readiness.md) and [Local training handoff](local-training-handoff.md).

## Why This Exists

Grona now has training examples, dataset packages, training plans, artifact bundles, dry-run trainer previews, backend boundaries, optional plugin stubs, and an experimental LoRA backend skeleton. Before real training is attempted, those pieces need an explicit readiness audit that can answer:

- Is the dataset package compatible with the training plan?
- Is the training plan compatible with the artifact bundle?
- Is the artifact bundle compatible with the backend?
- Does the backend support or reject the adapter config explicitly?
- Are required artifacts present?
- Are provenance, license, validation, and review fields preserved?
- Is execution still blocked by default?
- Which future real-training contract remains missing?

## Main Records

`TrainingPipelineStageStatus` records one stage:

- stage name
- status: `passed`, `warning`, `blocked`, or `not_checked`
- reasons
- metadata

`TrainingPipelineReadinessReport` records the full audit:

- `ready`
- `stage_statuses`
- `warnings`
- `blockers`
- `metadata`
- `summary`

`TrainingPipelineContract` describes what future real training must respect:

- required inputs
- required artifact paths
- required metadata fields
- required backend behavior
- forbidden default behavior
- future real-training requirements

`TrainingPipelineAuditor` evaluates the deterministic training-preparation pipeline without execution.

## Checked Stages

The audit checks these stages:

- `reviewed_trace_examples`
- `training_dataset_package`
- `training_artifacts`
- `training_plan`
- `dry_run_trainer`
- `backend`
- `safety`
- `provenance`
- `license`
- `validation`
- `execution`

## Compatibility Checks

The audit checks that:

- the dataset package has at least one train example
- the training export manifest exists and has examples
- dataset and model card drafts exist where expected
- training plan validation is available and valid
- training plan dataset metadata matches the package manifest
- required artifact paths are present
- backend required artifacts exist in the bundle
- backend supports or rejects the adapter type explicitly
- backend dependency status is reported instead of silently assumed
- safety config blocks execution by default
- provenance exists on training examples
- license summaries exist in manifests/configs where available
- raw, rejected, or unreviewed examples are not treated as training-ready

## Backend Contract Helper

`validate_training_backend_contract(backend, training_plan, artifact_bundle)` checks one backend boundary. It returns a `TrainingPipelineStageStatus` instead of raising for normal readiness blockers.

It checks:

- backend name and type
- capabilities
- required artifacts
- dependency report
- adapter support decision
- artifact compatibility
- readiness result

A backend that claims full readiness without explicit execution safety confirmation is treated as blocked. That is intentional: real training should remain impossible to trigger accidentally.

## Lifecycle Summary

`training_lifecycle_markdown()` returns a deterministic text summary:

```text
reviewed traces -> examples -> dataset package -> artifact bundle -> training plan -> dry-run -> backend readiness -> future real training
```

The broader handoff lifecycle adds explicit environment readiness and local handoff:

```text
reviewed traces -> training examples -> dataset package -> artifacts -> training plan -> dry-run -> backend boundary -> environment readiness -> local handoff -> future real training
```

## Demo

```bash
python -m grona --training-pipeline-audit-demo
python -m grona --model-build-readiness-demo
python examples/training_pipeline_audit_demo.py
python examples/model_build_readiness_demo.py
```

The training pipeline demo builds deterministic examples, a dataset package, training plan, artifact bundle, experimental LoRA backend, safety config, pipeline audit report, backend contract validation, and contract summary.

The model-build readiness demo adds environment readiness, artifact summary, backend readiness, blockers, warnings, and a local handoff checklist.

Neither demo writes files or executes training.

## Limitations

- no actual training
- no model loading
- no tokenizer loading
- no heavy ML dependency imports
- no subprocess execution
- no shell command execution
- no network calls
- no downloads or uploads
- no environment or GPU probing
- no guarantee real LoRA/QLoRA training will work yet
- no production certification

This layer is a contract audit and readiness map, not a trainer.
