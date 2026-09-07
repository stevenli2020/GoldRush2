# Tranche 3 Phase B — Filtering Criteria and Exclusion Log

**Status:** proposed; Phase B blocked pending D/Q approval

## Selection Boolean

A variable is a Phase B target iff all conditions are true:

```text
Status == ADMIT
AND variable has an implemented GR2 extractor/current JSON
AND frequency in {Monthly, Quarterly}
AND its evidence rule is affected by the approved 36/120, 48/132, or 12/40 minimum
AND it is not L6-001 (already handled in Phase A)
```

The resulting target set is exactly the 18 IDs in `TRANCHE3_PHASEB_TARGET_VARIABLES.md`.

## Explicit exclusions requested by D

| Variable | Exclusion reason |
|---|---|
| L0-007 Producer Hedging | Not present as an implemented GR2 ADMIT extractor/current JSON; no auditable frequency contract to recalibrate. |
| L0-008 Vaulted Gold | Not present as an implemented GR2 ADMIT extractor/current JSON; no auditable frequency contract to recalibrate. |
| L3-008 Inflation Surprise | Not present as an implemented GR2 ADMIT extractor/current JSON; no implemented monthly/quarterly evidence window in GR2. |
| L4-010 Treasury Issuance | Appears as an unmapped variable in legacy analytics material, but is not an implemented ADMIT extractor/current JSON in the current GR2 registry. |
| L7-002 Global Broad Money | Not present as an implemented GR2 ADMIT extractor/current JSON; therefore no current monthly/quarterly output can be safely refreshed. |

## Other exclusions

All other implemented variables are excluded for the same Boolean reason: daily/weekly/event-driven/annual frequency, non-window-related rule, no current extractor, or L6-001 Phase A ownership. No additional monthly/quarterly implemented variable is silently omitted from the 18-ID target list.
