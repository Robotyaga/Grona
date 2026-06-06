# Model Build Readiness

Grona now has a consolidated model-build readiness layer for deciding whether the repository is ready to move into local development for future explicit-only LoRA or QLoRA work.

This layer does not train models. It does not load models, execute commands, call APIs, download datasets, download model weights, upload artifacts, or write files by default.

## What It Checks

`ModelBuildReadinessReport` combines several already-safe layers:

- `TrainingPipelineAuditor` for reviewed examples, dataset package, artifacts, training plan, backend boundary, safety, provenance, license, validation, and execution blocking.
- `TrainingEnvironmentAuditor` for an explicit, user-described hardware and dependency profile.
- `validate_training_backend_contract()` for backend metadata, artifact requirements, dependency report, and readiness behavior.
- `ExperimentalLoRABackend` readiness when that backend is used.
- artifact bundle summary.
- training plan validation.
- local handoff manifest.

The report has two distinct readiness flags:

- `ready_for_real_training`: false by default. It should remain false until a real trainer exists, dependencies are available locally, safety gates are explicit, and local validation has passed.
- `ready_for_local_handoff`: true when the deterministic pipeline, in-memory artifacts, plan, and docs are complete enough to continue work in a local IDE.

## Environment Readiness

The environment layer is planning metadata, not hardware probing.

It includes:

- `TrainingHardwareProfile`
- `TrainingDependencyProfile`
- `TrainingEnvironmentProfile`
- `TrainingHardwareRequirement`
- `TrainingEnvironmentReadinessReport`
- `TrainingEnvironmentAuditor`

Requirement presets are conservative and descriptive:

- CPU dry-run
- small LoRA
- small QLoRA
- full fine-tune placeholder

These presets are not universal real-world guarantees. They are stable planning checks for deciding what is obviously missing before future local work.

## Why Real Training Is Still Blocked

Real training remains blocked because Grona still intentionally lacks:

- a production trainer implementation
- model loading logic
- subprocess or shell execution paths
- automatic downloads
- local GPU validation
- final model/dataset license review
- evaluation and rollback policy

This is deliberate. The current repository is ready for local handoff, not production model training.

## How Artifacts And Plans Fit

The readiness layer expects the existing deterministic flow:

```text
reviewed traces -> training examples -> dataset package -> artifacts -> training plan -> dry-run -> backend boundary -> environment readiness -> local handoff -> future real training
```

Artifacts are built in memory by default. `TrainingArtifactWriter` still requires explicit caller action for file writes.

## Safe Demo

Run:

```bash
python -m grona --model-build-readiness-demo
```

This prints:

- pipeline readiness
- environment readiness
- backend readiness
- artifact summary
- blockers
- warnings
- local handoff checklist

It does not execute real training.
