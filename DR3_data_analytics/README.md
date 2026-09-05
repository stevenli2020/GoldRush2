# DR3 — Data Analytics

DR3 combines current variable signals into one score, confidence level, and availability measure for each horizon.

Canonical implementation:

- [`config/weights_v1.yaml`](../config/weights_v1.yaml) — versioned variable weights.
- [`src/goldrush2/analytics/`](../src/goldrush2/analytics/) — aggregation models and engine.
- [`src/goldrush2/cli/analyze.py`](../src/goldrush2/cli/analyze.py) — `gr2 analyze` command.
- [`data/current/current_scores.json`](../data/current/current_scores.json) — latest output.

The approved V1.1 design rationale is in [`DR3_PROPOSAL_zh.md`](../DR3_PROPOSAL_zh.md). Run `gr2 analyze` after the required DR2 extractors have produced current JSON outputs.
