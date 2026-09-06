# Tranche 3 Step 4 Phase A Supplement

**Scope:** L6-001 only  
**Execution date:** 2026-09-07

## Schedule-estimated activation

The source cache had no machine-readable vintage date. Its recorded retrieval timestamp was `2026-09-04T14:20:43Z` (Friday). Under the approved Monday update schedule, the extractor calculated:

```json
{
  "vintage_date": null,
  "availability_source": "schedule_estimated",
  "estimated_availability_date": "2026-09-07",
  "retrieved_at": "2026-09-04T14:20:43Z"
}
```

The controlled refresh command was:

```bash
wsl bash -lc 'cd /mnt/d/Projects/GoldRush2 && .venv/bin/gr2 extract L6-001 --force -vvv --pretty'
```

## Signal delta

| Horizon | Phase A before | Supplement after | Delta interpretation |
|---|---|---|---|
| 1-5d | signal `0`, confidence `0`, `STALE` | signal `+1`, confidence `1.0`, `VALID` | schedule estimate activated the signal |
| 1-3m | signal `0`, confidence `0`, `STALE` | signal `+1`, confidence `0.7`, `VALID` | schedule estimate activated the signal with qualitative horizon confidence |
| 1-3y | signal `0`, confidence `0`, `NOT_APPLICABLE` | unchanged | long horizon remains disabled |
| 3-10y | signal `0`, confidence `0`, `NOT_APPLICABLE` | unchanged | long horizon remains disabled |

The latest observation remains `2026-09-01`. The estimated availability date is exactly the current Monday, so the result is valid without treating retrieval time as a publication date. `vintage_date` and `publication_date` remain null.

## Anti-leakage verification

SHA-256 and nanosecond modification timestamps were captured for every non-L6 JSON before extraction and compared after extraction.

| Scope | Files checked | Hash changes | mtime changes | Result |
|---|---:|---:|---:|---|
| All other `data/current/*.json` files | 44 | 0 | 0 | PASS |

The current directory contained 44 non-L6 files at this run (the earlier Phase A run contained 43). Every one remained byte-identical and untouched.

## Scope boundary

Only L6-001 was extracted. Phase B and Phase C were not run, and no strategy analysis was executed.
