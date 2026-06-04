# Growth Lab

Growth Lab is the research foundation for future self-growing modular intelligence in Grona.

The long-term idea is:

```text
DatasetSource -> DatasetSample -> KnowledgeSeed -> validation
-> deduplication/conflict checks -> review decision -> grape cluster assignment
-> GrowthEngine recommendations -> memory bridge / expert proposal review
-> feedback -> benchmarks -> optional training data export
```

The current implementation adds deterministic local-first foundations for `DatasetSource`, `DatasetSample`, `InstructionDatasetSample`, `ConversationDatasetSample`, `KnowledgeSource`, `KnowledgeSeed`, `ValidationResult`, `KnowledgeValidator`, `KnowledgeDeduplicator`, `KnowledgeConflictDetector`, `KnowledgeReviewPipeline`, `GrapeNode`, `GrapeCluster`, `GrapeAssignment`, `GrapeClusterer`, `GrowthDecision`, `GrowthPlan`, and `GrowthEngine`.

## Dataset Ingestion Foundation

Dataset ingestion is a normalization layer before Growth Lab seed review.

Current dataset structures:

- `DatasetSource`: provenance, source type, format, license, language, reliability, and metadata.
- `DatasetSample`: normalized content, sample type, domains, keywords, and metadata.
- `InstructionDatasetSample`: Alpaca-like instruction/input/output records.
- `ConversationDatasetSample`: ShareGPT/LMSYS-like role/content conversations.
- `AlpacaFormatAdapter`: deterministic in-memory adapter for Alpaca-like dictionaries.
- `ShareGPTFormatAdapter`: deterministic in-memory adapter for conversation dictionaries.

The adapters work only with small in-memory dictionaries. They do not download datasets, read files, call Hugging Face, parse Parquet, call external APIs, train models, or create artifacts.

Dataset samples become `KnowledgeSeed` values through `knowledge_seed_from_dataset_sample()` or `knowledge_seeds_from_dataset_samples()`. This preserves dataset format, license, language, source type, and sample type in metadata.

This matters because a dataset row may be an instruction, conversation, writing sample, or synthetic answer rather than factual knowledge. Grona should review it before it influences memory, benchmarks, expert behavior, or future training data.

See [Dataset ingestion](dataset-ingestion.md) for the dedicated design note.

## What Is a KnowledgeSeed?

A `KnowledgeSeed` is a raw piece of knowledge that Grona may ingest from a dataset sample, user note, document chunk, donor model output, tool result, feedback record, benchmark observation, or unknown source.

It is not trusted memory yet.

A seed carries content, source, domains, keywords, confidence, status, and metadata.

Suggested statuses are:

- `new`
- `validated`
- `weak`
- `quarantined`
- `rejected`
- `promoted`

## What Is a KnowledgeSource?

A `KnowledgeSource` describes where a seed came from: dataset source, user note, document, donor model, tool result, feedback, benchmark, or unknown source.

Each source has a simple reliability score from `0.0` to `1.0`. This is a local heuristic, not a proof of truth.

## Why Seeds Are Not Trusted Memory Yet

Raw knowledge can be incomplete, stale, contradictory, generic, low-confidence, duplicated, synthetic, license-sensitive, or from a weak source. Grona should not automatically promote raw input into durable memory or expert behavior.

The seed layer makes raw knowledge visible before promotion. It lets Grona quarantine, merge, or reject weak inputs instead of silently mixing them into a model prompt or training set.

## Validation

`KnowledgeValidator` is deterministic and standard-library only. It checks empty content, content length, source reliability, seed confidence, missing domains, missing keywords, generic content, and unknown source type.

It returns `ValidationResult` with accepted flag, status, score, reasons, warnings, and metadata.

This is not web fact-checking. It does not call external APIs, search the internet, run models, or verify factual truth.

## Normalization and Deduplication

`KnowledgeDeduplicator` creates `NormalizedKnowledge` for each seed by lowercasing text, trimming whitespace, collapsing repeated whitespace, removing trivial punctuation for matching, and normalizing keywords/domains.

It can detect exact normalized content duplicates, same-source exact duplicates, high keyword overlap inside the same domain, and highly similar short statements.

Duplicate results are represented as `DuplicateCheckResult`. A duplicate is not automatically deleted. It becomes a merge candidate so future memory or cluster layers can preserve provenance.

## Potential Conflict Detection

`KnowledgeConflictDetector` is conservative and deterministic. It looks for possible contradiction patterns when seeds share a domain and overlapping keywords or text.

Current examples include opposite polarity around terms such as supports / does not support, enabled / disabled, allowed / blocked, true / false, available / unavailable, safe / unsafe, and works / does not work.

A conflict result means potential conflict, not factual falsity. The detector does not know which claim is true. It only marks candidates that should not be promoted blindly.

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

## GrowthEngine MVP

`GrowthEngine` is the first deterministic growth decision layer. It receives reviewed seeds, review decisions, candidate grape clusters, and assignment traces, then returns a `GrowthPlan`.

A `GrowthDecision` includes:

- id
- target type
- target id
- action
- confidence
- reasons
- metadata

The current engine can recommend:

- `promote_seed`
- `merge_duplicate`
- `quarantine_seed`
- `reject_seed`
- `create_candidate_cluster`
- `strengthen_cluster`
- `mark_cluster_needs_review`
- `create_memory_record`
- `suggest_expert_candidate`
- `no_action`

These are recommendations only. The engine does not mutate seeds, clusters, memory, modules, routing metadata, tools, model weights, or training data.

## GrowthPlan and Memory Bridge

`GrowthPlan` is a deterministic bundle of `GrowthDecision` values with a summary and metadata. Its `to_text()` method prints a readable explanation for demos and CLI output.

`memory_records_from_growth_plan(plan, clusters)` prepares `MemoryRecord` values only for clusters that received `create_memory_record` decisions. It does not persist those records or promote them into trusted memory automatically.

This bridge connects GrowthEngine recommendations to the existing deterministic memory path while keeping human review and future policy gates possible.

## Expert Candidate Suggestions

`GrowthEngine` can emit `suggest_expert_candidate` when a cluster has enough reviewed seeds, enough confidence, and strong domain consistency.

This is not automatic expert creation. It is an auditable proposal for future review. No model is trained, no model weights are changed, and no expert module is created automatically.

## Conversions

The current layer can convert existing prototype outputs into raw seeds:

- `knowledge_seed_from_dataset_sample(sample)`
- `knowledge_seeds_from_dataset_samples(samples)`
- `knowledge_seed_from_document_chunk(chunk, source)`
- `knowledge_seed_from_tool_result(result, source)`

This connects dataset ingestion, document ingestion, and mock tool output to the future Growth Lab without making them trusted memory automatically.

## CLI Demos

```bash
python -m grona --growth-demo
python -m grona --growth-review-demo
python -m grona --grape-demo
python -m grona --growth-engine-demo
python -m grona --dataset-demo
```

The dataset demo prints dataset sample counts, generated seed counts, validation statuses, clusters, assignments, and GrowthEngine decisions.

## Examples

```bash
python examples/knowledge_seed_demo.py
python examples/knowledge_review_demo.py
python examples/grape_cluster_demo.py
python examples/growth_engine_demo.py
python examples/dataset_ingestion_demo.py
```

The dataset ingestion example shows `DatasetSource` creation, Alpaca-like and ShareGPT-like adapters, conversion into `KnowledgeSeed` values, validation, review, clustering, and GrowthEngine planning.

## How This Prepares Future Growth

`GrowthEngine` gives Grona a controlled recommendation layer between candidate clusters and future changes to memory, routing, experts, or training-data exports.

The important boundary is that recommendations stay explicit and reviewable. Humans can still review important structural changes before they affect durable memory, modules, or training data.

Deduplication matters because clusters should not over-weight repeated copies of the same claim. Conflict detection matters because a cluster should not blindly absorb two opposite claims as equal nutrients. Growth decisions make the next step visible instead of automatic.

## Why Dataset Samples Could Become Seeds

Future sources such as `yahma/alpaca-cleaned`, UA-Alpaca, OpenHermes, LMSYS / ShareGPT, Loghub, C4 slices, and Wikipedia-derived samples may contain useful examples, claims, formats, or task traces.

They should enter Grona as `DatasetSample` values and then `KnowledgeSeed` values with license and provenance metadata. That keeps dataset material inspectable before it becomes memory, benchmark material, expert behavior, or future training data.

## Why Donor Model Outputs Could Become Seeds

A donor model may later suggest summaries, labels, examples, or candidate facts. Grona can store those outputs as `KnowledgeSeed` values with `source_type="donor_model"` and a source reliability score.

That output should be validated, deduplicated, reviewed, optionally assigned to candidate clusters, and evaluated by GrowthEngine before it becomes memory, benchmark material, expert behavior, or training data.

## Current Limitations

- No autonomous self-training.
- No automatic expert creation.
- No model weights.
- No real dataset downloads.
- No Hugging Face integration or `datasets` dependency.
- No JSONL file loader or Parquet reader.
- No large dataset files or generated dataset artifacts.
- No web fact-checking.
- No temporal freshness checks.
- No semantic embeddings.
- No vector database.
- No LLM-based contradiction detection.
- No external evidence lookup.
- No automatic truth resolution.
- No real donor model integration.
- No persisted seed store.
- No persisted cluster store.
- No persisted growth plan store.
- No semantic clustering.
- No automatic promotion from cluster to trusted memory or expert behavior.
- No production knowledge-quality claims.

The current Growth Lab layer is a deterministic heuristic prototype for future experiments.
