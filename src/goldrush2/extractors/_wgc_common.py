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
    for pattern in ("%b %Y", "%B %Y"):
        try:
            return datetime.strptime(text, pattern).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def parse_official_changes_workbook(path: Any) -> list[dict[str, Any]]:
    """Read canonical country/date changes from the WGC Monthly sheet."""
    from openpyxl import load_workbook

    workbook = load_workbook(path, read_only=True, data_only=True)
    if "Monthly" not in workbook.sheetnames:
        raise ValueError("WGC Monthly sheet was not found")
    rows = list(workbook["Monthly"].iter_rows(values_only=True))
    header_index = next((index for index, row in enumerate(rows) if len(row) > 1 and str(row[1]).strip().lower() == "country"), None)
    if header_index is None:
        raise ValueError("WGC Monthly country header was not found")
    dates = [(index, parse_date(value)) for index, value in enumerate(rows[header_index]) if index >= 3 and parse_date(value) is not None]
    if not dates:
        raise ValueError("WGC Monthly date columns were not found")
    records: list[dict[str, Any]] = []
    for row in rows[header_index + 1 :]:
        country = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
        if not country or country.lower() == "nan" or country.endswith("*"):
            continue
        for column, observation_date in dates:
            value = row[column] if column < len(row) else None
            if value in (None, "") or not finite(value):
                continue
            records.append({"country": country, "date": observation_date, "value": float(value)})
    if not records:
        raise ValueError("WGC Monthly sheet contained no canonical numeric changes")
    return records


def parse_official_holdings_workbook(path: Any) -> list[dict[str, Any]]:
    """Read the two canonical entity panels from the WGC PDF sheet."""
    from openpyxl import load_workbook

    workbook = load_workbook(path, read_only=True, data_only=True)
    if "PDF" not in workbook.sheetnames:
        raise ValueError("WGC PDF sheet was not found")
    rows = list(workbook["PDF"].iter_rows(values_only=True))
    header_index = next((index for index, row in enumerate(rows) if {str(value).strip().lower() for value in row if value is not None} >= {"tonnes", "% of reserves**", "holdings as of"}), None)
    if header_index is None:
        raise ValueError("WGC official-holdings header was not found")
    records: list[dict[str, Any]] = []
    seen_countries: set[str] = set()
    for panel, name_index, tonnes_index, share_index, date_index, rank_index in (("left", 1, 2, 3, 4, 0), ("right", 6, 7, 8, 9, 5)):
        for row in rows[header_index + 1 :]:
            name = str(row[name_index]).strip() if name_index < len(row) and row[name_index] is not None else ""
            if not name or name.lower() in {"none", "nan", "total", "aggregate"}:
                break
            if name in seen_countries:
                continue
            if rank_index >= len(row) or not finite(row[rank_index]):
                break
            tonnes = row[tonnes_index] if tonnes_index < len(row) else None
            if not finite(tonnes) or float(tonnes) < 0:
                raise ValueError(f"Invalid official holdings for {name}")
            raw_share = row[share_index] if share_index < len(row) else None
            if isinstance(raw_share, str):
                raw_share = raw_share.split(")", 1)[-1].strip()
            if finite(raw_share) and not 0 <= float(raw_share) <= 1:
                raise ValueError(f"Invalid reserve share for {name}")
            share_value = float(raw_share) if finite(raw_share) else None
            source_date = row[date_index] if date_index < len(row) else None
            seen_countries.add(name)
            records.append({"country": name, "panel": panel, "date": parse_date(source_date), "source_date": str(source_date) if source_date is not None else None, "holdings": float(tonnes), "share": share_value})
    if not records:
        raise ValueError("WGC official-holdings sheet contained no valid records")
    return records


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
    rising_signal: int = 1,
    falling_signal: int = -1,
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
            signal, direction = rising_signal, "rose"
        elif change < 0:
            signal, direction = falling_signal, "fell"
        else:
            signal, direction = 0, "was unchanged"
        percentage_text = f"{change_pct:+.2f}%" if change_pct is not None else "percentage change unavailable"
        summary = f"{value_label} {direction} by {abs(change):.2f} ({percentage_text}), {'bullish' if signal == 1 else 'bearish' if signal == -1 else 'neutral'} for gold."
        if cached:
            summary += " SOURCE UNAVAILABLE — cached data used."
        horizons[horizon] = {"signal": signal, "confidence": 1, "evidence": {"data": {"current_value": current_value, "current_date": str(current["date"]), "comparison_value": comparison_value, "comparison_date": str(comparison["date"]), "change_absolute": change, "change_pct": change_pct}, "summary": summary}}
    return {"variable_id": variable_id, "as_of_date": as_of_date or date.today().isoformat(), "source_name": source_name, "source_url": source_url, "data_frequency": "Monthly", "observation_date": str(current["date"]) if current else None, "horizons": horizons}
