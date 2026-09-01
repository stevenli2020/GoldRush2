# Phase 4 Variable Tracker

Master sequence: the 44 admitted IDs in `docs/phase3-ai-evidence/closure/canonical_dataset.jsonl`, matched to `docs/phase3-ai-evidence/closure/variable_register.json` and sorted numerically by layer and variable number.

Neither closure file contains short names. Descriptions are copied from the matching entries in `docs/phase1-registry/Phase1-master-registry.md`; no conditional variables are added.

All rule, horizon, status and commit fields start blank for this walkthrough, including previously implemented variables. Record actual results only after the owner supplies the requested WSL output. Use `N/A` only for registry-excluded horizons. Record a real commit hash (linked to its GitHub commit) after commit/push confirmation; do not advance to the next task before both successful test output and that confirmation.

| # | Variable ID | Description | Rule Summary | 1-5d | 1-3m | 1-3y | 3-10y | Status | Commit Hash |
|---|-------------|-------------|--------------|------|------|------|-------|--------|-------------|
| Task 1 | L0-001 | Above-Ground Gold Stock | Annual stock delta. Short horizons (1-5d, 1-3m) → 0 (neutral). Long horizons → sign of delta (-1 if stock rose). | ✅ | ✅ | ✅ | ✅ | ✅ Pass | 131b47881ad73a0da11db1062dadf64eb66f39cd |
| Task 2 | L0-002 | Central-Bank Gold Holdings | Aggregate World monthly holdings. Short horizons -> 0; 1-3m latest vs 3m MA; 1-3y 3m vs 36m MA; 3-10y 12m vs 120m MA; fallback >=12m. | 0 | +1 | +1 | +1 | Closed | 53c65a8f3bb5f8e37c571dabee18d7c266802026 |
| Task 3 | L0-003 | Gold ETF Holdings | | | | | | | |
| Task 4 | L0-005 | Bar-and-Coin Investment Holdings / Demand | | | | | | | |
| Task 5 | L0-006 | Gold Recycling Flow | | | | | | | |
| Task 6 | L0-009 | Gold Lease Rates / Forward Rates | | | | | | | |
| Task 7 | L1-001 | 10Y TIPS Real Yield | | | | | | | |
| Task 8 | L1-002 | 5Y TIPS Real Yield | | | | | | | |
| Task 9 | L1-003 | Forward Real Rates | | | | | | | |
| Task 10 | L1-005 | Treasury Term Premium | | | | | | | |
| Task 11 | L1-006 | Expected Policy Rate | | | | | | | |
| Task 12 | L1-007 | 5Y5Y Forward Real Rate | | | | | | | |
| Task 13 | L2-001 | DXY US Dollar Index | | | | | | | |
| Task 14 | L2-002 | Broad Trade-Weighted Nominal US Dollar Index | | | | | | | |
| Task 15 | L2-003 | USD/CNY | | | | | | | |
| Task 16 | L3-001 | Fed Funds Futures Expected Policy Rate | | | | | | | |
| Task 17 | L3-002 | OIS Forward Policy Curve | | | | | | | |
| Task 18 | L3-003 | Expected Terminal Policy Rate | | | | | | | |
| Task 19 | L3-004 | Probability Distribution of Future Policy Outcomes | | | | | | | |
| Task 20 | L3-005 | FOMC Dot Plot Path | | | | | | | |
| Task 21 | L3-006 | FOMC Statements / Forward-Guidance Signal | | | | | | | |
| Task 22 | L4-001 | CPI Inflation Rate | | | | | | | |
| Task 23 | L4-002 | Core PCE Inflation Rate | | | | | | | |
| Task 24 | L4-003 | 5Y Breakeven Inflation | | | | | | | |
| Task 25 | L4-004 | 10Y Breakeven Inflation | | | | | | | |
| Task 26 | L4-006 | Fiscal Deficit / GDP | | | | | | | |
| Task 27 | L4-007 | Debt / GDP | | | | | | | |
| Task 28 | L4-008 | Interest Expense / Government Revenue | | | | | | | |
| Task 29 | L4-009 | Treasury Maturity Structure | | | | | | | |
| Task 30 | L5-001 | Monthly Official-Sector Gold Purchase Volume | | | | | | | |
| Task 31 | L5-002 | Gold Share of Official Reserves | | | | | | | |
| Task 32 | L5-003 | Reserve Composition Change / USD Share Change | | | | | | | |
| Task 33 | L5-006 | Official-Sector Gold Sales / Lending | | | | | | | |
| Task 34 | L6-001 | Active Conflict and Escalation Signal | | | | | | | |
| Task 35 | L6-002 | Sanctions and Sovereign-Asset Freeze Events | | | | | | | |
| Task 36 | L7-001 | Major Central-Bank Balance-Sheet Liquidity | | | | | | | |
| Task 37 | L7-003 | Global Private Non-Financial Credit Growth | | | | | | | |
| Task 38 | L7-004 | Credit-Spread Financial Stress | | | | | | | |
| Task 39 | L7-005 | Treasury Repo Funding Stress | | | | | | | |
| Task 40 | L8-001 | Gold ETF Net Flows | | | | | | | |
| Task 41 | L9-001 | Shanghai Gold Exchange Premium/Discount | | | | | | | |
| Task 42 | L9-004 | India Physical Gold Imports and Consumer Demand | | | | | | | |
| Task 43 | L10-001 | COMEX Managed-Money Net Positioning | | | | | | | |
| Task 44 | L10-002 | COMEX Gold Futures Open Interest | | | | | | | |

Walkthrough policy (owner instruction, 2026-08-31): allow stale observations with `STALE_DATA=True`; when a requested offset is unavailable, use the longest available own-series offset with `HORIZON_APPROX=True` and show the actual offset. Current scalars and panels/events receive an explicit documented anchor or primary-component rule during their task. Preserve existing quality flags and frozen Phase 3 evidence; make variable-local changes and keep unrelated worktree changes out of task commits.

Before any agent-run staging, commit or push, obtain the owner's confirmation. Until then this tracker records preparation only, not 44/44 completion.
