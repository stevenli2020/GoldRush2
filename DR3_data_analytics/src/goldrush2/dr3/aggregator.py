"""Small signal aggregation helper used by downstream score reporting."""
from __future__ import annotations

from typing import Any


def aggregate_signals(signals: list[dict[str, Any]], horizon: str) -> dict[str, Any]:
    valid = [item for item in signals if item.get("signal") is not None and float(item.get("confidence", 0)) > 0]
    if not valid:
        return {"signal": 0, "confidence": 0, "evidence": {"warning": f"no valid signals for horizon {horizon}"}}
    confidence = sum(float(item.get("confidence", 0)) for item in valid) / len(valid)
    mean = sum(float(item["signal"]) for item in valid) / len(valid)
    signal = 1 if mean > 0 else -1 if mean < 0 else 0
    return {"signal": signal, "confidence": confidence, "evidence": {"valid_count": len(valid)}}
