# Prompting And Inference Traces

Grona now has a lightweight foundation for prompt construction and inference trace records. This layer exists so future local LLM experiments, baseline comparisons, and reviewed training-data candidates do not become opaque.

It is deterministic and offline by default.

## Main Concepts

`PromptTemplate` stores a named prompt template with a description, system template, user template, and metadata. It uses Python standard-library formatting with explicit allowed fields only. There is no Jinja, no prompt optimizer, and no external dependency.

`PromptBuilder` turns a task, optional `RoutingDecision`, optional `ContextItem` values, and optional workspace metadata into a `RenderedPrompt`.

`RenderedPrompt` keeps the rendered system prompt, user prompt, combined prompt text, template name, and metadata.

`InferenceTrace` records the prompt-facing interaction:

- task
- prompt template and rendered prompt
- adapter name
- model label
- response text
- error state
- routing summary
- selected modules
- context sources
- metadata

`InMemoryInferenceTraceStore` is for tests, demos, and explicit callers. `JsonlInferenceTraceStore` appends one trace JSON object per line only when a caller gives a path. There is no database.

## Default Templates

Built-in templates are intentionally small:

- `general_task`
- `routing_trace_summary`
- `grona_vs_monolith_baseline`
- `knowledge_seed_proposal`
- `training_example_review`

They are not optimized prompts. They are stable contracts for future experiments and trace review.

## Static Prompt Trace Demo

```bash
python -m grona --prompt-trace-demo
python examples/prompt_trace_demo.py
```

Both commands route a deterministic task, build route-scoped context, render a prompt, call `StaticLocalLLMAdapter`, create an `InferenceTrace`, and print a readable preview. They do not call LM Studio, external APIs, downloads, or training.

## Relationship To Inference Review

`InferenceTrace` is provenance. `InferenceReview` is a separate human review record attached to a trace.

`InferenceReviewPolicy` can make a deterministic eligibility decision after a human status, rating, flags, notes, or corrected response are present. Accepted and high-rated traces may become eligible as candidates. Unsafe, rejected, unreviewed, or still-needing-correction traces are blocked by default.

This separation is intentional: a trace is not automatically training data, not automatically a benchmark reference, and not automatically a knowledge seed candidate. See [Inference review foundation](inference-review.md).

## Relationship To Local LLM Baselines

`LocalLLMAdapter` describes an adapter contract. The prompt trace layer controls what text is sent to that adapter and records what came back.

The default prompt trace demo uses only `StaticLocalLLMAdapter`. `LMStudioCompletionAdapter` can be used by an explicit caller in the future, but it is not used by default or in CI.

## Relationship To TrainingDataExporter

`InferenceTrace` is provenance. It records an interaction.

`TrainingDataExporter` prepares conservative training example candidates after records have enough validation or review metadata.

A trace is not automatically training data. Converting traces into training candidates should require explicit review policy, provenance checks, and quality decisions.

## Inference Review Demo

```bash
python -m grona --inference-review-demo
python examples/inference_review_demo.py
```

The demo creates static traces, attaches accepted/corrected/unsafe review records, evaluates deterministic policy decisions, and prints a summary. It does not call real LLMs, APIs, databases, downloads, or training.

## Current Limits

- no real model calls by default
- no CI dependency on LM Studio
- no external APIs
- no automatic prompt optimization
- no answer quality judgment
- no LLM judge
- no training
- no automatic conversion of traces into training examples
- no automatic conversion of reviews into training examples
- no database or production trace store
- no database or production review store
- no streaming
- no hidden tool execution

These limits are deliberate. The goal is reproducible prompt/output provenance before model-backed behavior is added.
