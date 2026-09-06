# Tranche 3 Step 2 — L6-001 Source Contract and Evidence Rules (Draft)

**Status:** approved; Step 3 implementation in progress
**Variable:** L6-001 Geopolitical Risk

## Source contract

L6-001 currently uses the Caldara–Iacoviello **Recent GPR daily index**, specifically the `GPRD_ACT` series, from the authors' public data page: [Geopolitical Risk Index](https://www.matteoiacoviello.com/gpr.htm). The collector downloads a versioned `data_gpr_daily_recent[_YYYYMMDD].dta` link and normalizes its `date` and `GPRD_ACT` columns.

The source states that daily Recent GPR data are updated every Monday (next business day when Monday is a federal holiday), and that latest data are preliminary and subject to revisions. The source also recommends recording the download date and exposes dated vintages. Those source facts make the versioned file/update date the candidate availability evidence; local file mtime is not acceptable.

## Why Plan 1 flagged L6-001 stale

The current cache ends at `2026-09-01`. The extractor calculates `gap = date.today() - latest observation date` and applies a three-day hard stale cutoff. On the 2026-09-06 run, this is a five-day gap, so both short horizons are suppressed to confidence zero. The implementation does not retain source release/update metadata, does not distinguish a weekend/holiday publication schedule from a failed refresh, and falls back to an optional snapshot without a source-status field.

This is a source-availability contract gap, not evidence that geopolitical risk was zero.

## Proposed evidence rules

- **Quantity:** daily `GPRD_ACT` level, with the existing 5-day versus 20-day mean spread standardized by the 60-observation population standard deviation.
- **Publication alignment:** `observation_date` is the measured news day; `publication_date` must be the explicit source update/vintage date when captured from the dated download link or page metadata. `retrieved_at` and filesystem mtime are provenance only.
- **Freshness:** use the source's Monday/next-business-day schedule, including Tuesday after a Monday federal holiday. A latest observation within the expected weekly release window is not stale merely because a weekend intervenes. A five-day weekend-gap fixture is explicitly tested. If explicit source update/vintage evidence is unavailable or the gap exceeds the approved schedule tolerance, emit confidence zero. Filesystem mtime and `retrieved_at` are ignored.
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

## Approval questions

- Approve the original Recent GPR `GPRD_ACT` source rather than migrating to AI-GPR or ACLED?
- Approve the weekly freshness tolerance and explicit vintage-date provenance rule?
- Keep 1-3y and 3-10y `NOT_APPLICABLE` for L6-001, or commission a separate monthly aggregation method?
