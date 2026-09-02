"""Deterministic current-output builder for FOMC statements."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

try:
    import google.generativeai as genai  # optional; scorer supplies the error state when absent
except ImportError:  # pragma: no cover - environment dependent
    genai = None

VARIABLE_ID = "L3-006"
CACHE_PATH = Path("data/cache/L3-006.json")
OUTPUT_PATH = Path("data/current/L3-006.json")


def _base(latest: dict[str, Any], all_statements: list[dict[str, Any]]) -> dict[str, Any]:
    evidence = {"date": latest["date"], "rate_range": latest.get("rate_range"), "text": latest.get("text", ""), "url": latest.get("url", ""), "statement_count": len(all_statements)}
    horizons = {}
    for horizon in ("1-5d", "1-3m"):
        horizons[horizon] = {"signal": 0, "confidence": 0, "evidence": {**evidence, "reason": "AI scoring has not been run"}}
    for horizon in ("1-3y", "3-10y"):
        horizons[horizon] = {"signal": 0, "confidence": 0, "evidence": {**evidence, "reason": "FOMC statements do not inform this horizon"}}
    return {"variable_id": VARIABLE_ID, "data_frequency": "Event-driven", "source_name": "Federal Reserve FOMC Statement", "source_url": latest.get("url", ""), "observation_date": latest["date"], "ai_status": "not_run", "ai": None, "horizons": horizons}


def _merge_ai(base: dict[str, Any], existing: dict[str, Any] | None, force_refresh: bool) -> dict[str, Any]:
    if force_refresh or not isinstance(existing, dict) or existing.get("observation_date") != base["observation_date"] or existing.get("ai_status") != "success":
        return base
    merged = dict(base)
    merged["ai_status"] = existing.get("ai_status")
    merged["ai"] = existing.get("ai")
    for horizon, result in (existing.get("horizons") or {}).items():
        if horizon in merged["horizons"]:
            merged["horizons"][horizon] = result
    return merged


def build_output(statements: list[dict[str, Any]], existing: dict[str, Any] | None = None, force_refresh: bool = False) -> dict[str, Any]:
    if not statements:
        raise ValueError("L3-006 cache contains no statements")
    ordered = sorted(statements, key=lambda row: str(row["date"]))
    return _merge_ai(_base(ordered[-1], ordered), existing, force_refresh)


def run(cache_path: Path = CACHE_PATH, output_path: Path = OUTPUT_PATH, force_refresh: bool = False) -> dict[str, Any]:
    statements = json.loads(Path(cache_path).read_text(encoding="utf-8"))
    existing = json.loads(output_path.read_text(encoding="utf-8")) if output_path.exists() else None
    output = build_output(statements, existing, force_refresh)
    if force_refresh or output.get("ai_status") != "success":
        from goldrush2.ai.fomc_scorer import score_l3_006
        output = score_l3_006(force=force_refresh, cache_path=cache_path, output_path=output_path)
        return output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, output_path)
    return output


def extract(variable_id: str = VARIABLE_ID, force_refresh: bool = False) -> dict[str, Any]:
    if variable_id.upper() != VARIABLE_ID:
        raise ValueError(f"Unsupported variable: {variable_id}")
    return run(force_refresh=force_refresh)
