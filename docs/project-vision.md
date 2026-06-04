# Project Vision

Grona explores a local-first, modular direction for AI systems: route tasks through small, inspectable expert clusters instead of treating every request as work for one monolithic model.

This is a research vision, not a claim that the current prototype already provides real AI reasoning, training, or production orchestration.

## Long-Term Direction

The long-term goal is a system that can grow specialized capabilities in a controlled way:

- start with explicit modules and routing metadata
- attach structured knowledge sources and deterministic memory
- normalize dataset samples while preserving provenance, license, language, and sample type
- collect route traces, feedback, validation signals, review decisions, cluster assignments, growth decisions, and seed outcomes
- use donor models and local models as optional sources of proposals, not unquestioned authorities
- export validated traces or knowledge packs for future specialized expert training
- keep routing, context, safety, provenance, and limitations visible

## Why Grona Is Not Just a RAG Wrapper

A RAG wrapper usually centers on retrieval plus prompt assembly around one model. Grona is exploring a broader architecture question: which capability should be active, which context should be visible, which tools should be allowed, and how should feedback alter future routing?

Retrieval can become one nutrient source inside Grona, but it should not be the entire system. A workspace profile may activate document search, code review, media workflow, automotive diagnostics, or security modules differently even for similar task text.

Growth Lab adds another distinction: raw knowledge is not automatically trusted just because it was retrieved, downloaded, normalized from a dataset, or generated. It can first become a `KnowledgeSeed`, receive deterministic validation and review, stay weak, duplicated, conflicted, quarantined, or rejected, become eligible for candidate `GrapeCluster` grouping, and then receive a `GrowthEngine` recommendation before durable use.

## Why Knowledge Should Not Always Be Baked Into Weights

Model weights are powerful, but they are not always the best place for project-specific, changing, auditable, source-sensitive, or license-sensitive knowledge. External structured knowledge can be:

- inspected before use
- corrected without retraining
- versioned and validated
- scoped to a workspace
- cited or excluded from a route
- deduplicated before weighting
- quarantined before promotion
- grouped into candidate clusters before durable use
- evaluated as a memory bridge or expert candidate proposal
- used to generate future training examples only after quality checks

Grona should be able to grow useful external knowledge before deciding whether any of it belongs in a specialized model.

## Current Concepts

### Growth Lab

A controlled experimental environment for testing how modules, memory, feedback, tools, datasets, and validation loops evolve together. The current foundation is deterministic dataset ingestion, `KnowledgeSeed` validation, review, grape cluster candidate grouping, and GrowthEngine recommendations.

### DatasetSource and DatasetSample

`DatasetSource` records dataset provenance, source type, format, license, language, reliability, and metadata. `DatasetSample` is the normalized internal sample that can become a raw Growth Lab seed.

Instruction and conversation dataset samples are represented explicitly before normalization. Alpaca-like and ShareGPT-like adapters currently work with tiny in-memory dictionaries only.

Dataset ingestion does not download real datasets, call Hugging Face, train models, or add model weights. It preserves provenance so future decisions can remain inspectable.

### KnowledgeSeed

A structured unit of external knowledge with source, domain, metadata, confidence, and validation status. A seed is not automatically trusted; it is material for routing, retrieval, validation, review, clustering, growth planning, or training data preparation.

### KnowledgeValidator

A layer for checking whether imported knowledge is coherent, source-aware, useful for a domain, and safe to use in a specific workspace. The current validator is simple deterministic scoring, not fact-checking.

### KnowledgeReviewPipeline

A deterministic layer for normalizing seeds, detecting duplicate candidates, marking potential conflicts, and recommending whether a seed should be promoted, merged, quarantined, rejected, or reviewed. It is not automatic truth resolution.

### GrapeCluster

A deterministic candidate group of related `GrapeNode` values formed from promote-candidate reviewed seeds. The current implementation groups by primary domain and keyword overlap, keeps assignment traces, and can bridge cluster summaries into memory records.

A `GrapeCluster` is not yet an autonomous expert, a training unit, or a semantic embedding cluster.

### GrowthEngine

A deterministic recommendation layer that proposes next actions from reviewed seeds, review decisions, grape clusters, and assignment traces. It can recommend seed promotion, duplicate merge, quarantine, rejection, cluster strengthening, memory-record preparation, cluster review, and expert-candidate proposals.

GrowthEngine does not automatically mutate modules, memory, routing metadata, clusters, tools, model weights, or training data. It prepares auditable recommendations for future review and policy gates.

### DonorModelAdapter and LMStudioAdapter

Future optional model interfaces. A donor model may suggest summaries, labels, examples, or candidate knowledge, but Grona should validate, deduplicate, review, cluster, evaluate with GrowthEngine, and trace those outputs before using them as durable project knowledge.

### TrainingDataExporter

A future export path for validated traces, examples, corrections, and structured knowledge. The aim is to create training material for specialized experts without hiding provenance.

## Research Posture

Grona should stay honest:

- no production claims before production capabilities exist
- no sandboxing claims before real isolation exists
- no learning claims before learning is measurable
- no dataset claims before downloads, licenses, and provenance policies are explicit
- no tool-use claims before real tool boundaries are implemented and tested
- no knowledge-quality claims without validation, review, clustering traces, growth decisions, and provenance
- no training claims before training data and evaluation are explicit

The current repository is the foundation: deterministic routing, dataset ingestion, memory, orchestration, workspaces, seed validation, seed review, candidate grape clustering, GrowthEngine recommendations, mock execution, safety planning, tests, and docs.
