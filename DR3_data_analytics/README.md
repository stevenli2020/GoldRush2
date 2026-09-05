# DR3 — Data Analytics

DR3 combines current variable signals into one score, confidence level, and availability measure for each horizon.

Canonical implementation:

- [`config/weights_v1.yaml`](config/weights_v1.yaml) — versioned variable weights.
- [`src/goldrush2/dr3/analytics/`](src/goldrush2/dr3/analytics/) — aggregation models and engine.
- [`src/goldrush2/dr3/analyze.py`](src/goldrush2/dr3/analyze.py) — `gr2 analyze` command.
- [`data/current_scores.json`](data/current_scores.json) — latest output.
- [`config/strategies/`](config/strategies/) — immutable sparse current-outlook strategy configurations.
- [`data/current/dr3_multi_strategy_outlook.json`](data/current/dr3_multi_strategy_outlook.json) — non-official comparison output from `gr2 analyze-strategies`.
- [`tests/`](tests/) — analytics tests.

The approved V1.1 design rationale is in [`DR3_PROPOSAL_zh.md`](DR3_PROPOSAL_zh.md). Run `gr2 analyze` after the required DR2 extractors have produced current JSON outputs.

`gr2 analyze-strategies` evaluates all 14 sparse strategies and the `SP-ALL` baseline from current DR2 signals only. It does not rank or select a strategy and does not change the existing official-score path.
