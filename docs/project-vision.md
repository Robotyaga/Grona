# Project Vision

Grona explores a local-first, modular direction for AI systems: route tasks through small, inspectable expert clusters instead of treating every request as work for one monolithic model.

This is a research vision, not a claim that the current prototype already provides real AI reasoning, training, benchmark accuracy, or production orchestration.

## Long-Term Direction

The long-term goal is a system that can grow specialized capabilities in a controlled way:

- start with explicit modules and routing metadata
- attach structured knowledge sources and deterministic memory
- normalize dataset samples while preserving provenance, license, language, and sample type
- collect route traces, feedback, validation signals, review decisions, cluster assignments, growth decisions, benchmark results, and seed outcomes
- use donor models and local models as optional sources of proposals, not unquestioned authorities
- compare Grona configurations with future monolithic model adapters through explicit benchmark reports
- export validated traces or knowledge packs for future specialized expert training
- keep routing, context, safety, provenance, benchmark assumptions, and limitations visible

## Why Grona Is Not Just a RAG Wrapper

A RAG wrapper usually centers on retrieval plus prompt assembly around one model. Grona is exploring a broader architecture question: which capability should be active, which context should be visible, which tools should be allowed, how should feedback alter future routing, and how should growth be measured?

Retrieval can become one nutrient source inside Grona, but it should not be the entire system. A workspace profile may activate document search, code review, media workflow, automotive diagnostics, or security modules differently even for similar task text.

Growth Lab adds another distinction: raw knowledge is not automatically trusted just because it was retrieved, downloaded, normalized from a dataset, generated, or scored by a benchmark. It can first become a `KnowledgeSeed`, receive deterministic validation and review, become eligible for candidate `GrapeCluster` grouping, receive a `GrowthEngine` recommendation, and then be measured by `BenchmarkSuite` before durable use.

## Current Concepts

### Growth Lab

A controlled experimental environment for testing how modules, memory, feedback, tools, datasets, validation loops, benchmarks, and growth decisions evolve together.

### BenchmarkSuite

A deterministic rubric and reporting layer for small local comparisons. It can compare baseline routing, demo memory, dataset seeds, grape clusters, GrowthEngine decisions, and orchestration traces without calling model APIs or external judges.

BenchmarkSuite does not prove answer quality. It prepares the measurement harness for future Grona-vs-monolith experiments.

### DatasetSource and DatasetSample

`DatasetSource` records dataset provenance, source type, format, license, language, reliability, and metadata. `DatasetSample` is the normalized internal sample that can become a raw Growth Lab seed.

Dataset ingestion does not download real datasets, call Hugging Face, train models, or add model weights.

### KnowledgeSeed, Review, GrapeCluster, and GrowthEngine

A `KnowledgeSeed` is structured external knowledge with source, domain, metadata, confidence, and validation status. It is not automatically trusted.

`KnowledgeReviewPipeline` normalizes seeds, detects duplicate candidates, marks potential conflicts, and recommends whether a seed should be promoted, merged, quarantined, rejected, or reviewed.

`GrapeCluster` groups promote-candidate reviewed seeds by deterministic domain and keyword overlap.

`GrowthEngine` proposes next actions from reviewed seeds and clusters. It does not mutate modules, memory, routing metadata, clusters, tools, model weights, or training data automatically.

## Research Posture

Grona should stay honest:

- no production claims before production capabilities exist
- no sandboxing claims before real isolation exists
- no learning claims before learning is measurable
- no benchmark accuracy claims before outputs, judges, and human review are explicit
- no dataset claims before downloads, licenses, and provenance policies are explicit
- no tool-use claims before real tool boundaries are implemented and tested
- no knowledge-quality claims without validation, review, clustering traces, growth decisions, benchmark traces, and provenance
- no training claims before training data and evaluation are explicit

The current repository is the foundation: deterministic routing, dataset ingestion, memory, orchestration, workspaces, seed validation, seed review, candidate grape clustering, GrowthEngine recommendations, BenchmarkSuite reports, mock execution, safety planning, tests, and docs.
