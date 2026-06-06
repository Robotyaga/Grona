# Fine-tuning Training Plan Scaffold

The training plan scaffold describes a possible future adapter or fine-tuning run without performing it.

It is configuration only. It does not train a model, load a model, call LM Studio, call external APIs, download datasets, download model weights, upload data, write artifacts by default, or add training libraries.

## Main Records

`BaseModelSpec` records the identity and policy metadata of a future base model:

- name
- provider
- model id
- parameter count label
- context length
- license
- intended use
- metadata

It never downloads or loads the model.

`AdapterTrainingSpec` records a future adapter plan:

- adapter type: `lora`, `qlora`, or `full_finetune_placeholder`
- rank
- alpha
- dropout
- target modules
- quantization label
- metadata

These are config values only, not an executable training backend.

`TrainingRunConfig` combines the base model, adapter plan, dataset package manifest, dataset summary, hyperparameter placeholders, evaluation plan, safety notes, output policy, seed, and metadata.

It supports:

- `to_dict()`
- `to_json()`
- readable summary text

`TrainingRunValidator` validates configuration only. It checks for missing training examples, missing license metadata, invalid adapter rank or alpha, invalid sequence length, missing safety notes, missing output policy, tiny datasets, and placeholder modes.

`TrainingRunValidationResult` stores:

- `valid`
- warnings
- errors
- metadata

`TrainingPlan` bundles the config, validation result, dataset card draft, optional model card draft, creation time, and metadata.

`ModelCardDraft` renders Markdown that clearly says the model is not trained. Its default training status is:

```text
not_trained_config_only
```

## Artifact Bundle Bridge

A validated `TrainingPlan` can now be paired with a `TrainingDatasetPackage` and passed to `TrainingArtifactBuilder`. That produces an in-memory [training artifact bundle](training-artifacts.md) with JSONL splits, config JSON, manifests, dataset/model card drafts, safety notes, and a bundle README.

The artifact bridge is still config-only. It does not train, load, download, upload, call APIs, or write files unless `TrainingArtifactWriter` is explicitly called with `dry_run=False`.

## Demo

```bash
python -m grona --training-plan-demo
python examples/training_plan_demo.py
```

The demo creates a deterministic tiny training dataset package, builds a QLoRA-like config scaffold, validates it, and prints a model card draft preview.

## Example

```python
from grona import build_demo_training_plan

plan = build_demo_training_plan()
print(plan.config.to_json())
print(plan.validation.to_text())
```

## Why This Exists

Grona can now create reviewed training candidates and deterministic dataset packages. Before any real training exists, the project needs an explicit planning boundary that captures:

- which base model would be considered
- which adapter strategy would be considered
- which dataset package would be used
- which licenses are visible
- which safety notes are attached
- which output policy would apply
- which warnings need human attention

This creates a reviewable bridge from dataset packages to future LoRA or QLoRA work without adding a training stack too early.

## Limitations

- no actual training
- no `torch`
- no `transformers`
- no `peft`
- no `bitsandbytes`
- no `datasets`
- no `accelerate`
- no model loading
- no model downloads
- no dataset uploads
- no artifact writing by default
- no real evaluation yet
- no production model card
- no guarantee that placeholder hyperparameters are good
- no claim that Grona can fine-tune models yet

Future training work should add a separate explicit backend only after the config, validation, dataset review, evaluation, hardware assumptions, and artifact policy are reviewed.
