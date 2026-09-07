# Tranche 3 Step 4 Phase A Report

**Scope:** L6-001 only  
**Execution date:** 2026-09-06

## Quarantine count clarification

The earlier report counted one network-sensitive test because it focused on the newly observed L6-001 failure. During final collection, L3-005 was found to use the same unmocked live-network fallback pattern. The final deterministic run therefore excluded exactly two tests, both recorded in `TEST_QUARANTINE.md`.

## Exact command

```bash
wsl bash -lc 'cd /mnt/d/Projects/GoldRush2 && .venv/bin/gr2 extract L6-001 --force -vvv --pretty'
```

Observed output: 15,219 observations; latest observation `2026-09-01`.

## Anti-leakage verification

Before extraction, SHA-256 and nanosecond modification timestamps were recorded for every JSON file in `DR2_data_extraction/data/current/` except `L6-001.json`. The complete machine-readable pre-refresh snapshot was `/tmp/gr2_phaseA_pre.json`; the post-refresh comparison was performed immediately after extraction.

| Scope | Files checked | Hash changes | mtime changes | Result |
|---|---:|---:|---:|---|
| All non-L6 current JSON files | 43 | 0 | 0 | PASS |

The comparison required both the SHA-256 digest and `st_mtime_ns` to match for every filename. No other current-variable file was modified, touched, or regenerated.

## L6-001 signal delta

| Horizon | Before refresh | After refresh | Source vintage |
|---|---|---|---|
| 1-5d | signal `+1`, confidence `0`, stale-gated cache | signal `0`, confidence `0`, `STALE` | `null` |
| 1-3m | signal `+1`, confidence `0`, stale-gated cache | signal `0`, confidence `0`, `STALE` | `null` |
| 1-3y | signal `0`, confidence `0`, disabled | signal `0`, confidence `0`, `NOT_APPLICABLE` | `null` |
| 3-10y | signal `0`, confidence `0`, disabled | signal `0`, confidence `0`, `NOT_APPLICABLE` | `null` |

The refresh did not activate a fresh signal. This is the safe result: the latest observation is 2026-09-01, but the collector did not provide explicit source vintage/update metadata. The extractor correctly refused to infer publication timing from retrieval time or filesystem metadata and suppressed the short-horizon signal. A `VALID` result requires a dated source vintage in a future controlled refresh.

## Scope boundary

Phase B and Phase C were not run. No other extractor or strategy-analysis command was executed.
