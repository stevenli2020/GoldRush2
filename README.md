# GoldRush2

GoldRush2 (GR2) is a Python-first personal gold-investment decision-support MVP. It produces current evidence and directional outlook inputs across four horizons; it does not execute trades.

## Project map

The project is organized around the five delivery stages. The `DR*` folders are the stage-oriented entry points: they explain each stage and link to its canonical live files. Runtime code remains in the standard Python locations so existing commands continue to work unchanged.

```text
DR1_definition/          Layer, variable, and scope definition
DR2_data_extraction/     DR2 source code, policy, data, diagnostics, and tests
DR3_data_analytics/      DR3 analytics code, weights, score output, and tests
DR4_data_presentation/   Score presentation and evidence-grounded reporting
DR5_operations/          CLI package root, end-to-end operation, and CLI tests

pyproject.toml           Shared Python package definition and CLI entry points
PROJECT.md               Project-wide scope and delivery contract
TRACKER.md               Project-wide roadmap and completion status
```

Read `AGENTS.md` before making changes. `PROJECT.md` is the project definition and `TRACKER.md` is the live roadmap. These project-wide documents remain at the root intentionally.

## Running GR2 from WSL

```bash
cd /mnt/d/Projects/GoldRush2
source .venv/bin/activate
set -a; source .env; set +a
gr2 collect --all --dry-run
gr2 extract --check
gr2 analyze
```

Use a specific collector or extractor when required:

```bash
gr2 collect L4-001
gr2 collect L4-001 --force
gr2 extract L0-006
gr2 extract L7-003 --pretty
```

`gr2 collect` writes source material to `DR2_data_extraction/data/raw/` and normalized data to `DR2_data_extraction/data/cache/`. `gr2 extract` discovers modules under `DR2_data_extraction/src/goldrush2/dr2/extractors/` and writes current variable JSON to `DR2_data_extraction/data/current/`. `gr2 analyze` reads those outputs with `DR3_data_analytics/config/weights_v1.yaml` and writes `DR3_data_analytics/data/current_scores.json`.

## Verification

```bash
pytest DR3_data_analytics/tests/test_aggregator.py -q
pytest -q
```
