# Project Vision

Grona explores a local-first, modular direction for AI systems: route tasks through small, inspectable expert clusters instead of treating every request as work for one monolithic model.

This is a research vision, not a claim that the current prototype already provides real AI reasoning, training, or production orchestration.

## Long-Term Direction

The long-term goal is a system that can grow specialized capabilities in a controlled way:

- start with explicit modules and routing metadata
- attach structured knowledge sources and deterministic memory
- collect route traces, feedback, validation signals, review decisions, cluster assignments, and seed outcomes
- use donor models and local models as optional sources of proposals, not unquestioned authorities
- export validated traces or knowledge packs for future specialized expert training
- keep routing, context, safety, provenance, and limitations visible

## Why Grona Is Not Just a RAG Wrapper

A RAG wrapper usually centers on retrieval plus prompt assembly around one model. Grona is exploring a broader architecture question: which capability should be active, which context should be visible, which tools should be allowed, and how should feedback alter future routing?

Retrieval can become one nutrient source inside Grona, but it should not be the entire system. A workspace profile may activate document search, code review, media workflow, automotive diagnostics, or security modules differently even for similar task text.

Growth Lab adds another distinction: raw knowledge is not automatically trusted just because it was retrieved or generated. It can first become a `KnowledgeSeed`, receive deterministic validation and review, stay weak, duplicated, conflicted, quarantined, or rejected, and only then become eligible for candidate `GrapeCluster` grouping.

## Why Knowledge Should Not Always Be Baked Into Weights

Model weights are powerful, but they are not always the best place for project-specific, changing, auditable, or source-sensitive knowledge. External structured knowledge can be:

- inspected before use
- corrected without retraining
- versioned and validated
- scoped to a workspace
- cited or excluded from a route
- deduplicated before weighting
- quarantined before promotion
- grouped into candidate clusters before durable use
- used to generate future training examples only after quality checks

Grona should be able to grow useful external knowledge before deciding whether any of it belongs in a specialized model.

## Future Concepts

### Growth Lab

A controlled experimental environment for testing how modules, memory, feedback, tools, and validation loops evolve together. The current foundation is deterministic `KnowledgeSeed` validation, review, and grape cluster candidate grouping.

### KnowledgeSeed

A structured unit of external knowledge with source, domain, metadata, confidence, and validation status. A seed is not automatically trusted; it is material for routing, retrieval, validation, review, clustering, or training data preparation.

### KnowledgeValidator

A layer for checking whether imported knowledge is coherent, source-aware, useful for a domain, and safe to use in a specific workspace. The current validator is simple deterministic scoring, not fact-checking.

### KnowledgeReviewPipeline

A deterministic layer for normalizing seeds, detecting duplicate candidates, marking potential conflicts, and recommending whether a seed should be promoted, merged, quarantined, rejected, or reviewed. It is not automatic truth resolution.

### GrapeCluster

A deterministic candidate group of related `GrapeNode` values formed from promote-candidate reviewed seeds. The current implementation groups by primary domain and keyword overlap, keeps assignment traces, and can bridge cluster summaries into memory records.

A `GrapeCluster` is not yet an autonomous expert, a training unit, or a semantic embedding cluster.

### GrowthEngine

A future controller that proposes additions or adjustments to modules, knowledge seeds, routing metadata, feedback rules, clusters, or training data. It should be auditable and conservative.

### DonorModelAdapter and LMStudioAdapter

Future optional model interfaces. A donor model may suggest summaries, labels, examples, or candidate knowledge, but Grona should validate, deduplicate, review, cluster, and trace those outputs before using them as durable project knowledge.

### TrainingDataExporter

A future export path for validated traces, examples, corrections, and structured knowledge. The aim is to create training material for specialized experts without hiding provenance.

## Research Posture

Grona should stay honest:

- no production claims before production capabilities exist
- no sandboxing claims before real isolation exists
- no learning claims before learning is measurable
- no tool-use claims before real tool boundaries are implemented and tested
- no knowledge-quality claims without validation, review, clustering traces, and provenance
- no training claims before training data and evaluation are explicit

The current repository is the foundation: deterministic routing, memory, orchestration, workspaces, seed validation, seed review, candidate grape clustering, mock execution, safety planning, tests, and docs.
