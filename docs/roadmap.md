# Roadmap

This roadmap keeps the project lightweight while leaving space for research-driven growth.

## Phase 0: Repository Foundation

- Initialize documentation and source layout.
- Add a minimal dependency-free router.
- Provide a basic routing demo.
- Keep project files readable for early contributors.

## Phase 1: Routing Experiments

- Add deterministic tests for expert ranking and top-k activation.
- Compare similarity functions for routing profiles.
- Add support for expert groups or local clusters.
- Record experiment notes in `docs/research-notes.md`.

## Phase 2: Expert Interfaces

- Define a common expert protocol for execution.
- Add examples for text, vector, and tool-like experts.
- Introduce optional dependency groups only when needed.
- Track routing decisions for debugging and evaluation.

## Phase 3: Evaluation

- Define metrics for activation sparsity, coverage, and task utility.
- Build small benchmark tasks for routing behavior.
- Compare sparse activation against dense baselines.
- Explore failure modes such as expert collapse and unstable routing.

## Phase 4: Learning and Adaptation

- Experiment with learned routing profiles.
- Add mechanisms for expert specialization over time.
- Investigate cluster-level activation and hierarchical routing.
- Evaluate whether modular growth improves capability without unnecessary compute.
