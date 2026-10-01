# Bounded research direction

The current product is persistent evidence memory. RSI is a research motivation,
not an established capability of this release.

## Useful next contributions

- Integrations that retain a framework's task and evidence identities while
  leaving authorization in its host adapter.
- Query and indexing improvements measured against reproducible local workloads,
  preserving revision conflicts and as-of semantics.
- Inspection tools that expose sources, contrary evidence, corrections, and
  retractions together.
- Clearer adapter documentation and tests for host transaction boundaries.

Discuss public API or schema changes in an issue before implementing them.

## Experiments to justify improvement claims

Connect actual task attempts and their independently evaluated outcomes to memory
versions. Compare repeated work with and without retained memory under comparable
budgets. Keep held-out evaluation tasks outside the proposal loop and retain failed
attempts alongside successes.

Potential measurements include repeated-failure rate, source-reference validity,
successful restoration, task completion, and resources consumed. Define each
measurement and its evaluation scope before reporting a gain. Delivery or retrieval
is a receipt, not a benefit measurement.

Later work may investigate how agents select, revise, and reuse memories. A complete
self-modifying runtime, foundation-model training, and trading strategies are not
part of this repository's current scope.
