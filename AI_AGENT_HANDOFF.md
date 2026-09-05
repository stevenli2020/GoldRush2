# GoldRush2 — AI Agent Handoff

Prepared: 2026-09-05 · Workspace snapshot: `main`, stage-based layout · Audience: incoming implementation and review agents.

## 1. Purpose and boundaries

GoldRush2 (GR2) is a Python-first personal gold-investment decision-support MVP. It collects evidence for 45 variables across 11 layers (L0–L10), produces per-variable directional signals, and aggregates four current outlook scores: `1-5d`, `1-3m`, `1-3y`, `3-10y`.

Signals are `-1 / 0 / +1`; aggregate scores range from -100 to +100. Scores describe weighted directional evidence, not return forecasts or calibrated probabilities. The system does not execute trades. Current outputs are overwritten; historical source observations are retained where required for lookbacks.

- Windows workspace: `D:\Projects\GoldRush2`
- WSL workspace: `/mnt/d/Projects/GoldRush2`
- Repository: https://github.com/stevenli2020/GoldRush2
- Runtime: Python >=3.11; existing WSL `.venv`; package/CLI: `goldrush2` / `gr2`.
- Credentials: project-root `.env`, ignored by Git. Never print, commit, or include values in handoffs.
- Design: simple, modular, free/public sources where practical, shared collectors, individual extractors. No speculative platform features or GR1 runtime dependencies.

## 2. GR1 background

GoldRush (GR1), at `D:\Projects\GoldRush`, supplied the causal framework, variable registry, ingestion research, and earlier scoring experiments. Its implementation includes Python and TypeScript plus more extensive phased governance.

Useful reference locations:

- `docs/gold_price_causal_model_v2_2.md`: causal model; distinguish underlying drivers, transmission channels, and amplifiers.
- `docs/phase1-registry/Phase1-master-registry.md`: original registry and source decisions.
- `docs/phase2-ingestion/`: source scripts, historical snapshots, and prior feasibility work.
- GR1 trackers: historical context only; do not infer GR2 completion from them.

GR2 is independent. Copying an explicitly approved source artifact for a backfill is different from reading GR1 files at runtime. Do not restore superseded GR1 status-only methods or manual qualitative scores merely because a reference script uses them. GR1 Layer 11 is outside GR2 scope.

## 3. Read order and current status

1. `AGENTS.md`: current working constraints.
2. `PROJECT.md`: project scope and intended contracts; contains older passages noted below.
3. `TRACKER.md`: current roadmap and DR3 completion.
4. `TRACKER_DR2_ARCHIVE.md`: detailed 45-variable inventory and historical verification; currently local/untracked.
5. `DR2_data_extraction/config/refresh_policies.yaml`, `DR3_data_analytics/config/weights_v1.yaml`: operational configuration.
6. `DR5_operations/src/goldrush2/paths.py`: authoritative locations for all stage-owned artifacts.
6. Relevant source code, tests, current JSON and metadata: verify actual behavior before changing it.
7. `DR3_PROPOSAL_zh.md`: approved design context; reconcile illustrative text against production code.

| Stage | Recorded state | Meaning |
|---|---|---|
| DR1 | Complete | 45-variable, 11-layer scope defined |
| DR2 | Complete, 45/45 | Extractors/collection paths exist; availability varies by source and horizon |
| DR3 | Complete; owner approved | v1.1 weights, aggregation, CLI and focused tests implemented |
| DR4 | Not started | Gemini narrative/report presentation remains pending; numeric scores already exist in DR3 |
| DR5 | Not started | Unified production orchestration and notifications remain pending |

Recorded verification from 2026-09-04: DR3 tests **8 passed**; full suite **800 passed, 1 failed**, at `tests/test_l6_001.py::test_snapshot_fallback`. These are historical results, not a fresh test run for this handoff.

The stage-based reorganization is the current workspace baseline. Generated caches, AI-score artifacts, newly downloaded raw-source files, and local archive notes may remain uncommitted by design. Run `git status --short` before beginning work and preserve unrelated local artifacts.

## 4. Architecture and artifacts

```text
External sources / owner datafeed
  → collectors → DR2_data_extraction/data/raw/ → normalized DR2_data_extraction/data/cache/ + metadata
  → individual extractors → DR2_data_extraction/data/current/L*.json
  → analytics + DR3_data_analytics/config/weights_v1.yaml → DR3_data_analytics/data/current_scores.json
  → future DR4 narrative → future DR5 orchestration
```

| Location | Responsibility |
|---|---|
| `DR2_data_extraction/src/goldrush2/dr2/collectors/` | Source retrieval, normalization, refresh and cache handling |
| `collectors/base.py` | Shared policy-driven cache behavior; custom collectors may override it |
| `DR2_data_extraction/src/goldrush2/dr2/extractors/l*.py` | Variable calculation, lookbacks, evidence, confidence and current output |
| `DR5_operations/src/goldrush2/cli.py` | `collect`, extractor discovery/dispatch, `analyze` registration |
| `DR3_data_analytics/src/goldrush2/dr3/analytics/` | Models and aggregation engine |
| `DR3_data_analytics/src/goldrush2/dr3/analyze.py` | Score display invoked by the DR5 CLI |
| `DR2_data_extraction/data/raw/` | Source files/responses; do not confuse with normalized histories |
| `DR2_data_extraction/data/cache/` | Historical observations, shared series, refresh metadata and some backups |
| `DR2_data_extraction/data/current/` | Latest per-variable signals and aggregate score file |
| `tests/`, `scripts/` | Tests, fixtures, diagnostic and backfill utilities |

Cache layouts vary: some use per-variable directories, others shared source directories or flat JSON files. Inspect path constants instead of assuming a uniform layout. Prefer atomic writes and preserve usable caches on source failure; some existing paths still write directly and need separate review.

## 5. Source and variable map

| Group | Variables / implementation notes |
|---|---|
| WGC / IMF IFS gold workbooks | L0-001 annual stock; L0-002 cumulative official net changes; L0-003 ETF holdings; L0-005 bar/coin demand; L0-006 recycling; L5-001 official purchases; L5-002 reserve-share proxy; L5-006 official reductions; L8-001 ETF flows; L9-001 China premium; L9-004 India demand/imports |
| FRED / FRB TIPS | L1-001 DFII10; L1-002 DFII5; L1-003 FRB forward-rate composite; L1-004 FRB TIPSY02; L1-005 THREEFFTP10; L1-007 derived forward real rate |
| Fed Funds futures / supplements | L1-006 CME ZQ implied rates with FRED supplements; L3-001 reuses its implied-rate history |
| Dollar | L2-001 Yahoo DX-Y.NYB; L2-002 FRED DTWEXBGS; L2-003 FRED DEXCHUS |
| OIS | L3-002 fixed 1Y rate; L3-003 fixed 2Y terminal proxy; shared historical/daily curves |
| Fed policy publications | L3-004 FedWatch CSV; L3-005 SEP median path; L3-006 FOMC statements and Gemini assessment |
| Inflation / fiscal | L4-001 CPIAUCSL; L4-002 PCEPILFE; L4-003 T5YIE; L4-004 T10YIE; L4-006 FYFSGDA188S; L4-007 GFDEGDQ188S; L4-008 Treasury MTS; L4-009 Treasury MSPD |
| Reserve composition | L5-003 IMF COFER world USD reserve share |
| Geopolitics | L6-001 deterministic GPRD_ACT proxy; L6-002 deterministic OFAC SDN changes |
| Liquidity / credit | L7-001 FRED WALCL; L7-003 BIS private credit; L7-004 high-yield OAS; L7-005 SOFR minus EFFR |
| Gold derivatives | L10-001 CFTC managed-money net positioning; L10-002 CFTC total futures open interest; shared Disaggregated Futures-Only history |
| Gold financing proxy | L0-009 specific near/far gold contracts from Yahoo plus daily FRED SOFR |

Methodology decisions to preserve:

- L0-009 uses two specific gold futures contracts, never one `GC=F` series for both legs. Proxy: `SOFR − (((far/near)^(365/days_between) − 1) × 100)`. Contract history and expiry approximation limit interpretation.
- L0-002 is a cumulative net-change index, not necessarily an absolute holdings stock. L5-002 lacks the reserve denominator and is excluded from DR3 to avoid duplicated evidence.
- L10-001/002 now use CFTC historical reports, superseding earlier CME Daily Bulletin proposals. Their weekly lookbacks are 5/13/52/260 observations, with graded confidence.
- L3-004 reads FedWatch CSV data. Current calendar lookbacks are 5/91/364/1820 days. A short CSV cannot supply multi-year history; forward-filling does not create earlier observations. Preserve meeting identity and probability-bucket semantics.
- L3-002/003 are directional OIS variables, superseding CME futures status-only implementations. Falling selected rates map to +1; rising rates to -1. A fixed 2Y OIS rate is an average-rate proxy, not a literal observed terminal policy rate.
- Horizon names do not imply universal offsets. Monthly, quarterly, weekly and daily extractors have different rules; an offset of N requires at least N+1 observations. Do not silently convert units or change economic definitions.

## 6. OIS history and daily accumulation

Approved flow: `CheckMySwap → owner Linux server → weekly GR2 retrieval`, with DTCC-derived historical curves supplying the earlier seed.

- Current local endpoint: `http://188.166.178.188/temp/datafeed/`.
- Query: `?from=YYYYMMDD&api_key=<daily value>`.
- Key rule: first 8 hexadecimal characters of SHA-256 of `OIS` + current `YYYYMMDD` in UTC+8. This is owner-accepted crawler deterrence, not secret authentication.
- Local collector: `DR2_data_extraction/src/goldrush2/dr2/collectors/ois.py`; logs mask the query key.
- Seed: `DR2_data_extraction/data/cache/dtcc/sofr_ois_curves_2y.json`.
- Combined cache: `DR2_data_extraction/data/cache/ois/ois_curves.json`.
- Raw response: `DR2_data_extraction/data/raw/dtcc/checkmyswap_latest.json`.
- Backfill utility: `scripts/backfill_dtcc_ois.py`.
- Server design: daily collector saves `data/YYYYMMDD.json`; PHP serves records from the requested date. Deployment and cron health require separate server verification; source files are not assumed present in this checkout.

Earlier work reported about two years beginning 2024-09-02. Count valid 1Y/2Y observations in the actual cache before claiming horizon coverage. Historical rates are DTCC transaction-derived estimates; CheckMySwap is a different construction/source. Preserve source labels, rate units, dates and tenor identity. The owner accepted the proxy/continuity caveat; acceptance does not establish perfect source equivalence.

Local OIS refreshes merge retained history, including forced refreshes. Base/FedWatch paths also contain backup/preservation changes, currently partly uncommitted. Verify each collector before using `--force`; do not generalize one class's protection to every source. Keep seed histories and manual CSVs available when onboarding a fresh clone.

## 7. CME authentication context

CME authentication previously succeeded, but authentication and dataset entitlements are separate. The historical working flow used root `.env` values `CME_API_ID` and `CME_API_KEY` (OAuth client password):

1. POST `grant_type=client_credentials` with HTTP Basic client credentials to `https://auth.cmegroup.com/as/token.oauth2`.
2. Use the returned access token as Bearer authentication for DataMine.
3. List: `https://datamine.new.cmegroup.com/api/list_entitlements_files`.
4. Download a discovered file ID: `https://datamine.new.cmegroup.com/cme/api/v2/download?fid=<file_id>`.

Daily Bulletin dataset code: `DLYBLLTN_DB`. Do not assume access includes historical settlements, FedWatch EOD, or true OIS. Earlier `/cme/api/v2/list`, invented COT endpoints and `X-API-Key` proposals were superseded. Read token expiry from the response; do not log tokens. Stale exported shell credentials previously caused reproducibility failures; reload `.env` or unset conflicting names before a diagnostic script that loads it itself.

## 8. DR3 v1.1 behavior

Let A be configured positive-weight, applicable variables for a horizon, and V the subset with available output and confidence C > 0. Missing variables stay in A. Explicit `evidence.data.applicable=false` removes a variable from A.

```text
score        = round(100 × ΣV(S × W × C) / ΣV(W × C))
availability = ΣV(W) / ΣA(W)
confidence   = ΣV(W × C) / ΣV(W)
```

No usable contributions produces score/confidence/availability zero and `DEGRADED`. Otherwise availability >=0.60 is `NORMAL`; below 0.60 is `DEGRADED`. Confidence is conditional on contributing data and must be read together with availability. It is not calibrated forecast accuracy.

- Weights: `DR3_data_analytics/config/weights_v1.yaml`, 35/35/44/44 entries across the four horizons.
- Nine structural exclusions in both shorter horizons: L0-001, L0-005, L0-006, L4-006, L4-007, L4-008, L5-003, L7-003, L9-004.
- L5-002 excluded across all horizons.
- Top-5 configured normalized weights are checked for missing/zero-confidence output before dropping unavailable contributors.
- `low_confidence_contributors` includes 0 < C < 0.5; graded 0.4 can be an intentional long-horizon setting, not necessarily a data shortage.
- `UNMAPPED` includes intentional omissions and repeats across horizons; the current warning lacks horizon context.
- DR4 must honor the agreed degraded-data reporting restriction. A CLI disclaimer alone does not implement the future report-generation gate.

Recorded user run: generated 2026-09-04 14:44 UTC; scores -3/-21/+1/-6, availability 87%/88%/89%/75%. These are a historical snapshot. Successful analysis only proves aggregation ran on existing JSON; it does not prove every source refreshed successfully.

## 9. WSL operating sequence

Inspect the dirty tree before pulling or changing branches. Existing environment:

```bash
cd /mnt/d/Projects/GoldRush2
source .venv/bin/activate
set -a
source .env
set +a
set -o pipefail
gr2 extract --check
gr2 collect --all --dry-run
gr2 collect --all -vvv 2>&1 | tee /tmp/gr2-collect.log
```

Review collection failures before interpreting results. Use `--force` only when a full refresh is intended and history protection is understood. Some extractors retrieve dependencies themselves; collection policies alone do not cover every source.

Run all discovered extractors and retain failure visibility:

```bash
failed=0
for file in DR2_data_extraction/src/goldrush2/dr2/extractors/l[0-9]*_[0-9]*.py; do
    name=$(basename "$file" .py)
    variable=$(printf '%s' "$name" | tr '[:lower:]_' '[:upper:]-')
    gr2 extract "$variable" -vvv 2>&1 | tee -a /tmp/gr2-extract.log || failed=1
done
printf 'Extraction failure flag: %s\n' "$failed"
# Inspect failures and degraded outputs before interpreting aggregation.
gr2 analyze 2>&1 | tee /tmp/gr2-analyze.log
python -m json.tool DR3_data_analytics/data/current_scores.json
```

This loop's lexical order covers the known L1-001/L1-002 → L1-007 and L1-006 → L3-001 sequence; it is not a general dependency scheduler. Other extractor-managed sources include FRB forward rates, term premium and SOFR/EFFR. There is no `gr2 extract --all` or `gr2 run-all` command yet. `pipefail` is needed so `tee` does not hide upstream failures.

`extract --force` is only forwarded to supported signatures; current dispatch recognizes `force_refresh`, not every extractor's `force` argument. Do not promise universal forced refresh or AI regeneration from the flag alone.

Validation commands:

```bash
pytest DR3_data_analytics/tests/test_aggregator.py -q
pytest -q
```

Fresh environment setup, if needed: `python3 -m venv .venv`, activate it, then `python -m pip install -e '.[dev]'`. Data seeds and credentials must be provisioned separately; installation does not reconstruct private/local artifacts.

## 10. Known issues and next-agent priorities

1. **Documentation drift:** `PROJECT.md` still defers the implemented DR3 formula, contains old deterministic-variable counts and describes all L6 variables as Gemini-derived. The current L6 implementations are deterministic. The DR2 archive contains historical status columns. Production weights/code and later owner decisions resolve these discrepancies; update documents surgically when assigned.
2. **L5-001 long horizon:** current evidence reports 295 monthly observations against a 756-month offset. This is roughly a 63-year requirement, not a three-year history gap. Review the intended method before promising more backfill as the solution. Similar unit issues warrant per-variable inspection.
3. **OIS and FedWatch history:** insufficient horizons must remain explicit; never synthesize pre-source data, backdate probabilities to meeting dates, or claim futures prices are OIS curves.
4. **Warnings/presentation:** repeated UNMAPPED warnings and absent horizon labels can mislead users. NORMAL means the coverage threshold passed, not that all sources are healthy or fresh.
5. **Source tests:** the previously failing GPR snapshot test needs reproduction and diagnosis in its own scope. Do not describe the full suite as clean.
6. **Evidence durability:** some cache-hardening work and data artifacts exist only locally. Audit and separately commit approved changes before treating a new clone as operationally equivalent.
7. **DR4/DR5:** next roadmap work is evidence-grounded reporting and reliable end-to-end orchestration. Both need concrete requirements, dependency/failure handling, and validation; neither is implemented by this document.

## 11. Collaboration protocol

- Work within the assigned scope; proposal, implementation, verification and owner approval are separate states.
- Read the latest task context and relevant files; do not repeat rejected source assumptions from older chat prompts.
- Preserve dirty worktrees, reconstructed histories and shared caches. Never bulk-stage or reset unrelated changes.
- Multiple agents should own distinct files/tasks and coordinate before touching shared CLI, policies, weights or trackers.
- Verify in WSL. Report source success versus cache fallback, observation date, horizon limitations, tests and commit/push status separately.
- Use compact professional handoffs and direct file/commit links. In this project conversation, responses conventionally start with `/goal`.

This handoff was assembled from repository documentation, current code and the recorded run history. No fresh network-source validation or production collection was performed to create it.
