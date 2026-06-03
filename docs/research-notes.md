# Research Notes

Grona explores modular sparse AI systems inspired by grape-cluster-like expert activation. These notes collect hypotheses, design questions, and experiment ideas.

## Working Hypothesis

A system with many small experts can remain efficient if routing activates only the experts relevant to the current context. The grape cluster metaphor suggests that expertise may be organized into local neighborhoods, where nearby experts are related but not identical.

## Early Questions

- What makes an expert sufficiently distinct from another expert?
- How many experts should be active for a given input?
- When should routing prefer a specialist over a generalist?
- Can local expert clusters reduce routing cost while preserving flexibility?
- How can the system avoid repeatedly selecting the same dominant experts?

## Experiment Ideas

### Toy Vector Routing

Represent experts and inputs as small vectors. Measure whether top-k routing selects expected experts across controlled examples.

### Cluster Activation

Group experts into clusters and compare direct expert routing with two-stage routing: first select clusters, then select experts inside those clusters.

### Diversity Penalty

Add a penalty when selected experts are too similar to each other. Measure whether diversity improves coverage without reducing relevance.

### Routing Trace Inspection

Record selected experts, scores, and skipped candidates for each input. Use traces to identify unstable or surprising activation patterns.

## Notes on Scope

The first version should not attempt to train large models or implement a full mixture-of-experts system. The priority is a clean conceptual and code foundation that makes later experiments easy to reason about.
