"""Shared helpers for monthly World Gold Council ETF extractors."""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any

HORIZON_LOOKBACKS = {"1-5d": 5, "1-3m": 63, "1-3y": 252, "3-10y": 756}


def finite(value: Any) -> bool:
    """Return whether a value can be represented as a finite float."""
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def parse_date(value: Any) -> str | None:
    """Normalize an Excel date or ISO-like string to YYYY-MM-DD."""
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    if value is None:
        return None
    text = str(value).strip()
    for parser in (date.fromisoformat,):
        try:
            return parser(text).isoformat()
        except ValueError:
            pass
    return None


def empty_data() -> dict[str, Any]:
    """Return the common empty evidence data shape."""
    return {"current_value": None, "current_date": None, "comparison_value": None, "comparison_date": None, "change_absolute": None, "change_pct": None}


def degraded(summary: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a zero-confidence horizon result."""
    return {"signal": 0, "confidence": 0, "evidence": {"data": data or empty_data(), "summary": summary}}


def build_output(
    variable_id: str,
    source_name: str,
    source_url: str,
    observations: list[dict[str, Any]],
    *,
    cached: bool = False,
    as_of_date: str | None = None,
    value_label: str,
) -> dict[str, Any]:
    """Build standard four-horizon monthly output using rising/falling direction."""
    ordered = sorted(observations, key=lambda item: str(item["date"]))
    current = ordered[-1] if ordered else None
    horizons: dict[str, Any] = {}
    for horizon, lookback in HORIZON_LOOKBACKS.items():
        if current is None or len(ordered) < lookback:
            data = empty_data()
            if current is not None:
                data.update({"current_value": float(current["value"]), "current_date": str(current["date"])})
            summary = f"MISSING DATA — {lookback} valid monthly observations are required; {len(ordered)} are available."
            if cached:
                summary += " SOURCE UNAVAILABLE — cached data used."
            horizons[horizon] = degraded(summary, data)
            continue
        comparison = ordered[-lookback]
        current_value, comparison_value = float(current["value"]), float(comparison["value"])
        change = round(current_value - comparison_value, 10)
        change_pct = round(change / comparison_value * 100, 10) if comparison_value else None
        if change > 0:
            signal, direction = 1, "rose"
        elif change < 0:
            signal, direction = -1, "fell"
        else:
            signal, direction = 0, "was unchanged"
        percentage_text = f"{change_pct:+.2f}%" if change_pct is not None else "percentage change unavailable"
        summary = f"{value_label} {direction} by {abs(change):.2f} ({percentage_text}), {'bullish' if signal == 1 else 'bearish' if signal == -1 else 'neutral'} for gold."
        if cached:
            summary += " SOURCE UNAVAILABLE — cached data used."
        horizons[horizon] = {"signal": signal, "confidence": 1, "evidence": {"data": {"current_value": current_value, "current_date": str(current["date"]), "comparison_value": comparison_value, "comparison_date": str(comparison["date"]), "change_absolute": change, "change_pct": change_pct}, "summary": summary}}
    return {"variable_id": variable_id, "as_of_date": as_of_date or date.today().isoformat(), "source_name": source_name, "source_url": source_url, "data_frequency": "Monthly", "observation_date": str(current["date"]) if current else None, "horizons": horizons}
