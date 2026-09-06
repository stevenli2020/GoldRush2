"""Render the fixed pre-audit matrix against a current sparse comparison run."""
from __future__ import annotations

import json
from pathlib import Path

from goldrush2.paths import DR3_MULTI_STRATEGY_OUTPUT_PATH, DR3_ROOT


HORIZONS = ("1-5d", "1-3m", "1-3y", "3-10y")
# Owner-recorded initial v1.1 comparison matrix, before input gating.
PRE_AUDIT_SCORES = {
    "SP-RATE": (-60.0, -70.0, -80.0, -60.0),
    "SP-USD": (40.0, 30.0, -80.0, 35.0),
    "SP-INFL": (-50.0, -80.0, -60.0, -60.0),
    "SP-CB": (60.0, -70.0, 60.0, -15.0),
    "SP-FLOW": (70.0, -70.0, 60.0, -20.0),
    "SP-TECH": (50.0, 60.0, 30.0, 65.0),
    "SP-REGIME-PROXY": (10.0, -10.0, -35.0, -32.0),
    "SP-ANTI-FIAT": (40.0, -20.0, 80.0, 40.0),
    "SP-MACRO": (-10.0, -30.0, -50.0, -20.0),
    "SP-L0L5": (60.0, -10.0, 60.0, -10.0),
    "SP-L6L7": (10.0, 50.0, -40.0, 15.0),
    "SP-SPARSE": (40.0, 0.0, 10.0, 0.0),
    "SP-SHORT": (70.0, -20.0, 5.0, -40.0),
    "SP-LONG": (60.0, -20.0, -10.0, -40.0),
    "SP-ALL": (2.2, 2.2, 2.2, -8.9),
}


def _format_score(value: float) -> str:
    return f"{value:+.1f}"


def render_report(comparison_path: Path = DR3_MULTI_STRATEGY_OUTPUT_PATH) -> str:
    current = json.loads(comparison_path.read_text(encoding="utf-8"))
    lines = [
        "# Sparse strategy score delta report",
        "",
        "This report compares the owner-recorded initial v1.1 matrix with the current current-outlook run after Plan 1 input gating, soft confidence decay, and the 70% usable-coverage threshold.",
        "It is a current-data diagnostic, not a backtest or a strategy ranking.",
        "",
        f"Generated from comparison run: `{current['generated_at']}`.",
        "",
        "| Strategy | Horizon | Pre-Audit Score | Post-Audit Score | Delta | Post Coverage | Status | Primary Zeroed Variables |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    degraded = 0
    for strategy_id, prior_scores in PRE_AUDIT_SCORES.items():
        current_strategy = current["strategies"][strategy_id]
        for horizon, prior in zip(HORIZONS, prior_scores):
            result = current_strategy["horizons"][horizon]
            score = float(result["score"])
            status = result["status"]
            degraded += status == "DEGRADED"
            zeroed = [
                f"{variable_id} ({entry['input_status'].lower()})"
                for variable_id, entry in result["contributions"].items()
                if entry["weight"] > 0 and entry["input_status"] != "VALID"
            ]
            lines.append(
                f"| {strategy_id} | {horizon} | {_format_score(prior)} | {_format_score(score)} | "
                f"{_format_score(score - prior)} | {result['usable_weight_coverage']:.0%} | {status} | "
                f"{', '.join(zeroed) if zeroed else '-'} |"
            )
    lines += [
        "",
        f"{degraded} of {len(PRE_AUDIT_SCORES) * len(HORIZONS)} strategy-horizon results are DEGRADED under the 70% threshold.",
        "A zeroed variable is excluded because the current run marks it stale, unavailable, invalid, missing, or inapplicable; it does not mean the underlying economic force is zero.",
        "",
    ]
    return "\n".join(lines)


def write_report(output_path: Path = DR3_ROOT / "SCORE_DELTA_REPORT.md") -> Path:
    output_path.write_text(render_report(), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    print(write_report())
