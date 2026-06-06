# Inference Review Foundation

Grona now has a lightweight human review layer for `InferenceTrace` records. It exists to keep prompt/output traces from becoming training material, benchmark references, or knowledge seed candidates without an explicit review decision.

This layer is deterministic and offline by default.

## Main Concepts

`InferenceReview` stores one human review for one trace:

- review id
- trace id
- creation timestamp
- reviewer label
- status
- optional 1-5 rating
- quality flags
- notes
- corrected response
- metadata

Supported statuses are:

- `accepted`
- `rejected`
- `needs_correction`
- `corrected`
- `unsafe`
- `not_reviewed`

Supported quality flags are:

- `factually_wrong`
- `incomplete`
- `off_topic`
- `unsafe`
- `hallucinated`
- `poor_format`
- `good_structure`
- `useful`
- `needs_sources`

## Policy Decisions

`InferenceReviewPolicy` evaluates one review with conservative deterministic rules and returns an `InferenceReviewDecision`.

The default policy:

- blocks `unsafe`, `rejected`, `needs_correction`, and `not_reviewed` reviews
- blocks reviews with missing or low ratings
- blocks accepted reviews with unsafe, hallucinated, factually wrong, or off-topic flags
- allows high-rated `accepted` reviews
- allows high-rated `corrected` reviews only when corrected responses are present and config allows them

A positive policy decision only means the record is eligible as a candidate for downstream use. It does not train a model, promote knowledge, prove factual correctness, or write benchmark files.

## Stores

`InMemoryInferenceReviewStore` is for tests, demos, and explicit callers.

`JsonlInferenceReviewStore` appends one review JSON object per line only when a caller provides a path. There is no database, service, or hidden persistence layer.

## Summary

`InferenceReviewSummary` reports:

- total reviews
- status counts
- average rating
- eligible-for-training count
- unsafe count
- corrected count
- rejected count

Eligibility counts are produced by applying the deterministic policy, not by trusting ratings alone.

## Demo

```bash
python -m grona --inference-review-demo
python examples/inference_review_demo.py
```

The demo creates static `InferenceTrace` records with the existing prompt trace runner, attaches accepted/corrected/unsafe reviews, evaluates policy decisions, and prints a summary.

It does not call real LLMs, LM Studio, APIs, downloads, training, databases, or web servers.

## Current Limits

- no automatic quality claims
- no LLM judge
- no automatic conversion of traces into training data
- no automatic benchmark reference creation
- no automatic knowledge seed promotion
- no database or service-backed review store
- no reviewer identity system
- no multi-review consensus policy yet

These limits are deliberate. The goal is to make human review explicit before future model-backed or training-related workflows are added.
