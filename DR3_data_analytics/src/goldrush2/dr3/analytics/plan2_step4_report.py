"""Render the controlled L4-001 refresh comparison for Plan 2 Step 4."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from goldrush2.paths import DR2_CURRENT_DIR, DR3_ROOT

HORIZONS = ("1-5d", "1-3m", "1-3y", "3-10y")


def _score(value: float) -> str:
    return f"{value:+.2f}"


def render(pre_path: Path, post_path: Path) -> str:
    pre = json.loads(pre_path.read_text(encoding="utf-8"))
    post = json.loads(post_path.read_text(encoding="utf-8"))
    l4 = json.loads((DR2_CURRENT_DIR / "L4-001.json").read_text(encoding="utf-8"))
    l4_data = l4["horizons"]["1-5d"]["evidence"].get("data", {})
    l4_summary = l4["horizons"]["1-5d"]["evidence"].get("summary", "")
    source_mode = "live FRED data" if "SOURCE UNAVAILABLE" not in l4_summary else "cached FRED data after source unavailability"
    lines = [
        "# Plan 2 Step 4 — L4-001 Controlled Refresh Comparison",
        "",
        "This report compares the frozen strategy run captured immediately before the L4-001 refresh with the unchanged strategy engine after the refresh.",
        "The comparison is current-outlook evidence, not a backtest or a strategy ranking.",
        "",
        f"L4-001 now uses publication-aligned `CPI_YoY_12m_MA` and emits `+0.5` for the refreshed {l4_data.get('CPI_YoY_12m_MA'):.2f}% smoothed rate. The refresh used {source_mode}; its latest smoothed observation is dated {l4_data.get('observation_date')} with publication date {l4_data.get('publication_date')}.",
        "",
        "| Strategy | Horizon | Pre Score | Post Score | Delta | L4 Pre Contribution | L4 Post Contribution | Post Coverage | Status |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for strategy_id, strategy in post["strategies"].items():
        for horizon in HORIZONS:
            before = pre["strategies"][strategy_id]["horizons"][horizon]
            after = strategy["horizons"][horizon]
            before_l4 = before["contributions"].get("L4-001", {}).get("contribution", 0.0)
            after_l4 = after["contributions"].get("L4-001", {}).get("contribution", 0.0)
            delta = after["score"] - before["score"]
            lines.append(f"| {strategy_id} | {horizon} | {_score(before['score'])} | {_score(after['score'])} | {_score(delta)} | {_score(before_l4)} | {_score(after_l4)} | {after['usable_weight_coverage']:.0%} | {after['status']} |")
    lines += [
        "",
        "## Interpretation",
        "",
        "- The L4-001 contribution changes from the old CPI index-direction output to the approved smoothed rate output. Because the refreshed `CPI_YoY_12m_MA` is 2.70%, L4-001 contributes a positive half-strength signal wherever its strategy weight is present.",
        "- The strategy configurations and horizon weights were not changed. Score deltas therefore arise from the L4-001 refresh and the explicit acceptance of the approved half-strength signal.",
        "- `DEGRADED` statuses remain data-coverage warnings; they are not converted into rankings or suppressed scores.",
        "",
        "## Next correction tranche",
        "",
        "Proceed to the shared monthly WGC tranche: L8-001 ETF flows and L5-001 official-sector purchases. Their current extractors reuse row-count lookbacks across monthly data, and both require publication-date contracts, calendar-aligned windows, and separate flow-versus-change semantics before implementation.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m goldrush2.dr3.analytics.plan2_step4_report PRE_JSON POST_JSON")
    output = DR3_ROOT / "PLAN2_STEP4_L4_COMPARISON.md"
    output.write_text(render(Path(sys.argv[1]), Path(sys.argv[2])), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
