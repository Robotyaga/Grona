# Architecture

Grona is designed around a sparse modular architecture. Instead of sending every input through one dense path, the system uses a router to activate a small set of experts from a larger pool.

## Conceptual Model

The architecture is inspired by a grape cluster:

- Each grape represents a specialized expert.
- Small local groups of grapes represent related expert neighborhoods.
- A cluster can activate only the experts that match the current input.
- The whole structure remains available, but only a sparse subset participates in each step.

This metaphor is meant to guide modularity and activation patterns, not to impose a biological model.

## Initial Components

### Router

The router receives an input representation and ranks available experts by relevance. The first implementation uses simple vector similarity so the behavior is transparent and easy to test.

### Expert

An expert is a small callable module with metadata and a routing profile. In future versions, experts may wrap learned models, symbolic tools, retrieval pipelines, or hybrid modules.

### Activation Result

Routing returns an ordered set of activated experts and their scores. This keeps routing explainable and makes it easier to debug activation behavior.

## Design Principles

- Sparse by default: activate a small subset of available experts.
- Modular boundaries: keep routing separate from expert execution.
- Inspectable behavior: expose scores and selected experts.
- Lightweight iteration: avoid heavyweight infrastructure until experiments justify it.

## Future Architecture Questions

- How should experts be grouped into local neighborhoods?
- Should routing use learned embeddings, handcrafted features, or both?
- How can experts share context without collapsing into dense global execution?
- What metrics best capture useful sparse activation?
