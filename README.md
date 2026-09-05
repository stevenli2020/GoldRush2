# GoldRush2

GoldRush2 (GR2) is a Python-first personal gold-investment decision-support MVP. It produces current evidence and directional outlook inputs across four horizons; it does not execute trades.

## Project map

The project is organized around the five delivery stages. The `DR*` folders are the stage-oriented entry points: they explain each stage and link to its canonical live files. Runtime code remains in the standard Python locations so existing commands continue to work unchanged.

```text
DR1_definition/          Layer, variable, and scope definition
DR2_data_extraction/     Source collection, normalization, and variable extraction
DR3_data_analytics/      Weighting and aggregation of variable outputs
DR4_data_presentation/   Score presentation and evidence-grounded reporting
DR5_operations/          End-to-end operation, user workflow, and notifications

src/goldrush2/           Executable Python package and the gr2 CLI
tests/                   Automated tests
scripts/                 One-off diagnostics and backfill utilities
config/                  Runtime collection policies and analytics weights
data/raw/                Latest source responses and downloaded workbooks
data/cache/              Normalized observations and refresh metadata
data/current/            Latest per-variable signals and aggregate scores
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

`gr2 collect` writes source material to `data/raw/` and normalized data to `data/cache/`. `gr2 extract` discovers `l<layer>_<variable>` modules under `src/goldrush2/extractors` and writes the current signal JSON to `data/current/`. `gr2 analyze` reads those current outputs and `config/weights_v1.yaml` to write `data/current/current_scores.json`.

## Verification

```bash
pytest tests/analytics/test_aggregator.py -q
pytest -q
```
