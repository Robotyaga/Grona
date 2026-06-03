# Growth Lab

Growth Lab is the research foundation for future self-growing modular intelligence in Grona.

The long-term idea is:

```text
raw knowledge -> KnowledgeSeed -> validation -> deduplication/conflict checks
-> grape cluster assignment -> memory/expert growth -> feedback -> benchmarks
-> optional training data export
```

The current implementation only adds the first safe deterministic layer: `KnowledgeSource`, `KnowledgeSeed`, `ValidationResult`, and `KnowledgeValidator`.

## What Is a KnowledgeSeed?

A `KnowledgeSeed` is a raw piece of knowledge that Grona may ingest from a user note, document chunk, donor model output, tool result, feedback record, benchmark observation, or unknown source.

It is not trusted memory yet.

A seed carries:

- content
- source
- domains
- keywords
- confidence
- status
- metadata

Suggested statuses are:

- `new`
- `validated`
- `weak`
- `quarantined`
- `rejected`
- `promoted`

## What Is a KnowledgeSource?

A `KnowledgeSource` describes where a seed came from:

- `user_note`
- `document`
- `donor_model`
- `tool_result`
- `feedback`
- `benchmark`
- `unknown`

Each source has a simple reliability score from `0.0` to `1.0`. This is a local heuristic, not a proof of truth.

## Why Seeds Are Not Trusted Memory Yet

Raw knowledge can be incomplete, stale, contradictory, generic, low-confidence, or from a weak source. Grona should not automatically promote raw input into durable memory or expert behavior.

The seed layer makes raw knowledge visible before promotion. It lets Grona quarantine or reject weak inputs instead of silently mixing them into a model prompt or training set.

## Validation

`KnowledgeValidator` is deterministic and standard-library only. It checks:

- empty content
- content length
- source reliability
- seed confidence
- missing domains
- missing keywords
- suspiciously generic content
- unknown source type

It returns `ValidationResult` with:

- accepted flag
- status
- score
- reasons
- warnings
- metadata

This is not web fact-checking. It does not call external APIs, search the internet, run models, or verify factual truth.

## Conversions

The current layer can convert existing prototype outputs into raw seeds:

- `knowledge_seed_from_document_chunk(chunk, source)`
- `knowledge_seed_from_tool_result(result, source)`

This connects document ingestion and mock tool output to the future Growth Lab without making them trusted memory automatically.

## CLI Demo

```bash
python -m grona --growth-demo
```

The command creates deterministic demo seeds, validates them, and prints counts for validated, weak, quarantined, and rejected seeds.

## Example

```bash
python examples/knowledge_seed_demo.py
```

The example shows direct seed creation, validation, document chunk conversion, and tool result conversion.

## How This Prepares GrapeCluster and GrowthEngine

Future `GrapeCluster` work can group validated seeds by domain, workspace, module, or tool profile.

Future `GrowthEngine` work can propose changes based on validated seeds and feedback, but it should remain auditable. The GrowthEngine should not silently mutate modules, memory, or training data.

## Why Donor Model Outputs Could Become Seeds

A donor model may later suggest summaries, labels, examples, or candidate facts. Grona can store those outputs as `KnowledgeSeed` values with `source_type="donor_model"` and a source reliability score.

That output should be validated before it becomes memory, benchmark material, or training data.

## Why Raw Data Can Be Messier Than Monolithic Training Data

A monolithic training pipeline often needs cleaner input before training because bad data can become hard to inspect later. Grona can tolerate rougher raw input at the seed stage because it can label, weight, quarantine, validate, and reject knowledge before promotion.

This does not make bad data good. It makes uncertainty explicit.

## Current Limitations

- No web fact-checking.
- No temporal freshness checks.
- No deduplication or conflict resolution yet.
- No automatic cluster growth.
- No training or model-weight changes.
- No real donor model integration.
- No embeddings or vector database.
- No persisted seed store.
- No production knowledge-quality claims.

The current Growth Lab layer is a deterministic validation foundation for future experiments.
