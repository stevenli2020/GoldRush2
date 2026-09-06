# Tranche 3 Step 2 — L6-001 Source Contract and Evidence Rules

**Status:** approved; Step 3 implemented
**Variable:** L6-001 Geopolitical Risk

## Source contract

L6-001 currently uses the Caldara–Iacoviello **Recent GPR daily index**, specifically the `GPRD_ACT` series, from the authors' public data page: [Geopolitical Risk Index](https://www.matteoiacoviello.com/gpr.htm). The collector downloads a versioned `data_gpr_daily_recent[_YYYYMMDD].dta` link and normalizes its `date` and `GPRD_ACT` columns.

The source states that daily Recent GPR data are updated every Monday (next business day when Monday is a federal holiday), and that latest data are preliminary and subject to revisions. The source also recommends recording the download date and exposes dated vintages. Those source facts make the versioned file/update date the candidate availability evidence; local file mtime is not acceptable.

## Why Plan 1 flagged L6-001 stale

The current cache ends at `2026-09-01`. The extractor calculates `gap = date.today() - latest observation date` and applies a three-day hard stale cutoff. On the 2026-09-06 run, this is a five-day gap, so both short horizons are suppressed to confidence zero. The implementation does not retain source release/update metadata, does not distinguish a weekend/holiday publication schedule from a failed refresh, and falls back to an optional snapshot without a source-status field.

This is a source-availability contract gap, not evidence that geopolitical risk was zero.

## Proposed evidence rules

- **Quantity:** daily `GPRD_ACT` level, with the existing 5-day versus 20-day mean spread standardized by the 60-observation population standard deviation.
- **Publication alignment:** `observation_date` is the measured news day; a real source `vintage_date` is strictly preferred. When the source lacks machine-readable version dates but provides its official Monday/next-business-day update schedule, the controlled `schedule_estimated` mode is permitted. In that mode `publication_date` and `vintage_date` remain null, while `estimated_availability_date` and `availability_source="schedule_estimated"` are recorded. `retrieved_at` is provenance and schedule input only; filesystem mtime is ignored.
- **Freshness:** estimate availability from the retrieved timestamp and the Monday/next-business-day schedule, including Tuesday after a Monday federal holiday. The estimate is valid only within the seven-day schedule tolerance; it does not grant infinite freshness. If the estimate is absent or exceeded, emit confidence zero and `STALE`. A five-day weekend-gap fixture is explicitly tested.
- **History:** require 60 valid daily observations for the 1-5d and 1-3m calculations, with no silent row compression across malformed dates. `1-3y` and `3-10y` are `NOT_APPLICABLE`.
- **Direction:** positive standardized recent-vs-medium spread → `+1`; negative → `-1`; exact zero → `0`. This is a geopolitical-risk level signal only; no policy or macro interpretation is added here.
- **Revision handling:** retain the source vintage/download URL and refresh the normalized cache when a newer dated vintage is available. Revisions must be visible in provenance.
- **Degradation:** missing source/update evidence, fewer than 60 valid observations, stale beyond the approved weekly tolerance, or parse failure → `signal=0`, `confidence=0`, explicit `STALE DATA`/`INSUFFICIENT HISTORY`/`SOURCE UNAVAILABLE`, and a status field identifying the cause.

## Required Step 3 tests

1. Monday update and Tuesday-after-holiday calendar fixtures remain fresh within the approved tolerance.
2. A five-day gap without source update metadata is stale and zero-confidence.
3. A dated source vintage is accepted as availability evidence; filesystem mtime is ignored.
4. Fewer than 60 valid daily observations degrades both short horizons.
5. Malformed/missing dates do not get compressed into a valid 60-row window.
6. Snapshot fallback is explicitly labelled and never appears as a fresh live source.

## Approved decisions

- Retain Caldara–Iacoviello `GPRD_ACT`; no migration to AI-GPR or ACLED in this tranche.
- Use Monday/next-business-day freshness tolerance with explicit source vintage/update dates only. Ignore filesystem mtime and `retrieved_at` for freshness.
- Keep `1-3y` and `3-10y` as `NOT_APPLICABLE` for L6-001.
