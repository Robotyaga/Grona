# Growth Lab

Growth Lab is the research foundation for future self-growing modular intelligence in Grona.

The long-term idea is:

```text
raw knowledge -> KnowledgeSeed -> validation -> deduplication/conflict checks
-> review decision -> grape cluster assignment -> memory/expert growth
-> feedback -> benchmarks -> optional training data export
```

The current implementation adds deterministic local-first foundations for `KnowledgeSource`, `KnowledgeSeed`, `ValidationResult`, `KnowledgeValidator`, `KnowledgeDeduplicator`, `KnowledgeConflictDetector`, `KnowledgeReviewPipeline`, `GrapeNode`, `GrapeCluster`, `GrapeAssignment`, and `GrapeClusterer`.

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

Raw knowledge can be incomplete, stale, contradictory, generic, low-confidence, duplicated, or from a weak source. Grona should not automatically promote raw input into durable memory or expert behavior.

The seed layer makes raw knowledge visible before promotion. It lets Grona quarantine, merge, or reject weak inputs instead of silently mixing them into a model prompt or training set.

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

## Normalization and Deduplication

`KnowledgeDeduplicator` creates `NormalizedKnowledge` for each seed by:

- lowercasing text
- trimming whitespace
- collapsing repeated whitespace
- removing trivial punctuation for matching
- normalizing keywords and domains

It can detect:

- exact normalized content duplicates
- same-source exact duplicates
- high keyword overlap inside the same domain
- highly similar short statements

Duplicate results are represented as `DuplicateCheckResult`. A duplicate is not automatically deleted. It becomes a merge candidate so future memory or cluster layers can preserve provenance.

## Potential Conflict Detection

`KnowledgeConflictDetector` is conservative and deterministic. It looks for possible contradiction patterns when seeds share a domain and overlapping keywords or text.

Current examples include opposite polarity around terms such as:

- supports / does not support
- enabled / disabled
- allowed / blocked
- true / false
- available / unavailable
- safe / unsafe
- works / does not work

A conflict result means potential conflict, not factual falsity. The detector does not know which claim is true. It only marks candidates that should not be promoted blindly.

Potential conflicts are represented as `ConflictCheckResult` with severity:

- `none`
- `low`
- `medium`
- `high`

## Review Decisions

`KnowledgeReviewPipeline` combines validation, deduplication, and potential conflict detection. It returns `SeedReviewDecision` objects with one of these decisions:

- `promote_candidate`
- `merge_duplicate`
- `quarantine_conflict`
- `quarantine_weak`
- `reject_broken`
- `needs_review`

The pipeline does not promote anything into real memory, clusters, tools, or training data. It only recommends the next review step.

## GrapeNode, GrapeCluster, and GrapeAssignment

`GrapeClusterer` is the first deterministic clustering layer after review decisions. It only assigns seeds whose review decision is `promote_candidate`.

Current structures:

- `GrapeNode`: a small organized candidate unit created from one reviewed seed.
- `GrapeCluster`: a deterministic group of related nodes inside one primary domain.
- `GrapeAssignment`: an explicit trace showing whether a seed was assigned, skipped, and why.

The current clusterer groups seeds by primary domain and deterministic keyword overlap. It calculates confidence from seed confidence, source reliability, cluster size, and simple penalties. This is explainable local scoring, not semantic clustering, model training, or expert creation.

Seeds with duplicate, weak, conflict, rejected, or manual-review decisions are not silently absorbed. They receive unassigned `GrapeAssignment` traces with a reason.

## Memory Bridge

`memory_records_from_grape_clusters(clusters)` converts candidate or active clusters into `MemoryRecord` values.

This bridge lets the existing deterministic memory and context path see reviewed cluster summaries without introducing embeddings, vector search, or persistent memory. It is a prototype bridge, not a claim that clusters have become trusted expert behavior.

## Conversions

The current layer can convert existing prototype outputs into raw seeds:

- `knowledge_seed_from_document_chunk(chunk, source)`
- `knowledge_seed_from_tool_result(result, source)`

This connects document ingestion and mock tool output to the future Growth Lab without making them trusted memory automatically.

## CLI Demos

Validation-only demo:

```bash
python -m grona --growth-demo
```

Review pipeline demo:

```bash
python -m grona --growth-review-demo
```

Grape cluster demo:

```bash
python -m grona --grape-demo
```

The review demo prints validation results, duplicate checks, potential conflict checks, review decisions, and counts by decision.

The grape demo prints deterministic cluster counts, nodes, assignments, and memory-record bridge counts.

## Examples

```bash
python examples/knowledge_seed_demo.py
python examples/knowledge_review_demo.py
python examples/grape_cluster_demo.py
```

The review example shows why some seeds become promote candidates while others are merge candidates, quarantined conflicts, weak quarantines, or rejected broken seeds.

The grape cluster example shows how promote-candidate seeds become `GrapeCluster` and `GrapeNode` values, then bridge into deterministic memory records.

## How This Prepares GrowthEngine

`GrapeCluster` now gives future GrowthEngine experiments a structured candidate layer between reviewed seeds and any future memory, routing, expert, or training-data changes.

Future `GrowthEngine` work can propose changes based on reviewed seeds, clusters, and feedback, but it should remain auditable. The GrowthEngine should not silently mutate modules, memory, or training data.

Deduplication matters because clusters should not over-weight repeated copies of the same claim. Conflict detection matters because a cluster should not blindly absorb two opposite claims as equal nutrients.

## Why Donor Model Outputs Could Become Seeds

A donor model may later suggest summaries, labels, examples, or candidate facts. Grona can store those outputs as `KnowledgeSeed` values with `source_type="donor_model"` and a source reliability score.

That output should be validated, deduplicated, reviewed, and optionally assigned to candidate clusters before it becomes memory, benchmark material, or training data.

## Why Raw Data Can Be Messier Than Monolithic Training Data

A monolithic training pipeline often needs cleaner input before training because bad data can become hard to inspect later. Grona can tolerate rougher raw input at the seed stage because it can label, weight, deduplicate, quarantine, validate, reject, and assign knowledge before promotion.

This does not make bad data good. It makes uncertainty explicit.

## Current Limitations

- No web fact-checking.
- No temporal freshness checks.
- No semantic embeddings.
- No vector database.
- No LLM-based contradiction detection.
- No external evidence lookup.
- No automatic truth resolution.
- No automatic expert growth.
- No training or model-weight changes.
- No real donor model integration.
- No persisted seed store.
- No persisted cluster store.
- No semantic clustering.
- No automatic promotion from cluster to trusted memory or expert behavior.
- No production knowledge-quality claims.

The current Growth Lab layer is a deterministic heuristic prototype for future experiments.
