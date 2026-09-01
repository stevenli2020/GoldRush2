"""Maturity-agnostic collection from the Federal Reserve Board TIPS curve CSV."""

from __future__ import annotations

import csv
import math
from datetime import date
from io import StringIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

FRB_TIPS_URL = "https://www.federalreserve.gov/data/yield-curve-tables/feds200805.csv"
DATA_DICTIONARY_ITEM = "NA42"


class FrbTipsError(RuntimeError):
    """Base error for Federal Reserve TIPS curve collection failures."""


class FrbTipsNetworkError(FrbTipsError):
    """Raised when the Federal Reserve Board source cannot be reached."""


class FrbTipsDataError(FrbTipsError):
    """Raised when the Federal Reserve Board returns malformed curve data."""


def _column_for_maturity(maturity: str) -> str:
    normalized = maturity.strip().upper()
    if not normalized.endswith("Y") or not normalized[:-1].isdigit():
        raise FrbTipsDataError(f"Unsupported TIPS maturity: {maturity}")
    return f"TIPSY{int(normalized[:-1]):02d}"


def parse_tips_yield(csv_text: str, maturity: str) -> list[dict[str, str | float]]:
    """Parse valid observations for one smoothed TIPS yield maturity."""
    lines = csv_text.splitlines()
    header_index = next(
        (index for index, line in enumerate(lines) if line.startswith("Date,")),
        None,
    )
    if header_index is None:
        raise FrbTipsDataError("Federal Reserve TIPS CSV has no Date header")

    column = _column_for_maturity(maturity)
    reader = csv.DictReader(StringIO("\n".join(lines[header_index:])))
    if reader.fieldnames is None or column not in reader.fieldnames:
        raise FrbTipsDataError(f"Federal Reserve TIPS CSV has no {column} column")

    observations: list[dict[str, str | float]] = []
    for position, row in enumerate(reader, start=1):
        observation_date = row.get("Date")
        raw_value = row.get(column)
        if raw_value in {None, "", ".", "NA", "N/A"}:
            continue
        try:
            date.fromisoformat(str(observation_date))
            value = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise FrbTipsDataError(
                f"Federal Reserve TIPS observation {position} is malformed"
            ) from exc
        if not math.isfinite(value):
            raise FrbTipsDataError(
                f"Federal Reserve TIPS observation {position} is not finite"
            )
        observations.append({"date": str(observation_date), "value": value})

    return observations


def _write_raw_csv(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_bytes(content)
    temporary_path.replace(path)


def fetch_tips_yield(
    maturity: str,
    *,
    raw_path: Path | None = None,
    timeout: float = 30,
) -> list[dict[str, str | float]]:
    """Fetch one maturity from the full TIPS curve and optionally cache the raw CSV."""
    request = Request(
        FRB_TIPS_URL,
        headers={"User-Agent": "GoldRush2/0.1 personal-investment-advisor"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            content = response.read()
    except HTTPError as exc:
        raise FrbTipsNetworkError(
            f"Federal Reserve TIPS request failed (HTTP {exc.code})"
        ) from exc
    except URLError as exc:
        raise FrbTipsNetworkError(
            f"Federal Reserve TIPS source is unavailable: {exc.reason}"
        ) from exc

    try:
        csv_text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise FrbTipsDataError("Federal Reserve TIPS source returned invalid text") from exc

    observations = parse_tips_yield(csv_text, maturity)
    if raw_path is not None:
        _write_raw_csv(raw_path, content)
    return observations


def load_cached_tips_yield(
    path: Path, maturity: str
) -> list[dict[str, str | float]]:
    """Load one maturity from a previously cached full TIPS curve CSV."""
    try:
        csv_text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        raise FrbTipsDataError(
            f"Cannot read cached Federal Reserve TIPS response: {path}"
        ) from exc
    return parse_tips_yield(csv_text, maturity)
