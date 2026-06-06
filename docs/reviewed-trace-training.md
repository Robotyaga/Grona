# Reviewed Trace Training Builder

`ReviewedTraceTrainingExampleBuilder` is the controlled bridge from reviewed inference traces into explicit `TrainingExample` candidates:

```text
InferenceTrace + InferenceReview + InferenceReviewPolicy -> TrainingExample candidate
```

This layer is deterministic and offline. It does not train a model, call a model, call LM Studio, call external APIs, download datasets, write files by default, or claim that generated examples are final high-quality training data.

## Why This Exists

Raw model output should not become training data just because it was recorded in an `InferenceTrace`.

A trace can become a training candidate only after:

- an explicit `InferenceReview` exists
- `InferenceReviewPolicy` marks the review eligible for training
- unsafe, rejected, unreviewed, or still-needing-correction reviews are excluded
- corrected reviews use `corrected_response`, not the original weak response
- provenance and review metadata are preserved

This gives future specialized Grona expert training a safer input boundary than raw prompt/output logs.

## Main Types

`ReviewedTraceTrainingExampleBuilder` evaluates one trace/review pair and either creates a `TrainingExample` or returns a skipped result.

`ReviewedTraceBuildResult` records:

- trace id
- review id
- whether an example was created
- optional `TrainingExample`
- policy and skip reasons
- metadata

`build_training_examples_from_reviews()` processes many traces and reviews in deterministic order. It handles missing reviews and orphan reviews without raising hidden errors.

`training_examples_from_build_results()` extracts created examples. `skipped_reviewed_trace_results()` extracts skipped results for reporting.

## Output Selection

Output text is chosen conservatively:

- `accepted` reviews use the original trace response text
- `corrected` reviews use `corrected_response`
- `needs_correction`, `rejected`, `unsafe`, and `not_reviewed` reviews do not create examples under the default policy

Corrected responses replace bad original responses because the original trace output was explicitly judged insufficient.

## TrainingExample Data

Created examples use:

- `instruction`: trace task
- `input`: rendered user prompt plus visible prompt/context metadata
- `output`: accepted response or corrected response
- `source`: `reviewed_inference_trace`
- `domains`: trace metadata when present
- `capabilities`: trace metadata when present
- `license`: explicit trace/review license metadata or `internal-reviewed-trace-demo`
- `validation_status`: `reviewed`

Provenance preserves:

- trace id
- review id
- adapter name
- model name
- prompt template name
- selected modules
- context sources

Metadata preserves:

- review status
- rating
- quality flags
- reviewer
- review notes when present
- policy decision data

## Demo

```bash
python -m grona --reviewed-trace-training-demo
python examples/reviewed_trace_training_demo.py
```

The demo creates deterministic static traces, attaches accepted, corrected, rejected, and unsafe reviews, builds training candidates, creates an in-memory `TrainingDataset`, and prints a native JSONL preview.

It does not write files or train anything.

## Current Limits

- no training
- no automatic quality guarantee
- no LLM judge
- no review UI
- no automatic model improvement
- no dataset upload
- no file writing by default
- no multi-review consensus logic
- no guarantee that examples are ready for real fine-tuning

These limits are deliberate. This is a provenance-preserving candidate builder, not a training system.
