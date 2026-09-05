"""CLI command: gr2 analyze"""
from __future__ import annotations
import argparse
import sys
from goldrush2.dr3.analytics.aggregator import run_analytics

def print_score_bar(score: int, width: int = 20) -> str:
    half = width // 2
    normalized = score / 100.0
    filled = int(abs(normalized) * half)
    if score >= 0: bar = " " * half + "|" + "+" * filled + "." * (half - filled)
    else: bar = "." * (half - filled) + "-" * filled + "|" + " " * half
    return bar

def run(args: argparse.Namespace) -> int:
    print("=" * 60)
    print("  GoldRush2 — DR3 Analytics Engine")
    print("=" * 60)
    try: result = run_analytics()
    except Exception as e:
        print(f"ERROR: Analytics failed: {e}", file=sys.stderr); return 1

    print(f"  Weight Schema: {result.weight_schema_version}")
    print(f"  Generated At:  {result.generated_at}\n")
    
    for horizon, hs in result.horizons.items():
        bar = print_score_bar(hs.score)
        status_mark = "🔴 DEGRADED" if hs.status == "DEGRADED" else "🟢 NORMAL"
        print(f"  {horizon:<6} [{bar}] {hs.score:+d} (Avail: {hs.data_availability:.0%}) [{status_mark}]")
        if hs.status == "DEGRADED":
            print(f"         ⚠️  DATA INSUFFICIENCY DISCLAIMER: Score relies on <60% of applicable evidence.")
        if hs.low_confidence_contributors:
            lc_str = ", ".join([f"{x['variable_id']}({x['confidence']:.1f})" for x in hs.low_confidence_contributors])
            print(f"         Low Conf: {lc_str}")
    print()
    if result.warnings:
        for w in result.warnings: print(f"  - {w}")
    print("\n  Output: DR3_data_analytics/data/current_scores.json")
    print("=" * 60)
    return 0
