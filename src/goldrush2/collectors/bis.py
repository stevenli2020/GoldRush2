"""BIS SDMX collector for global private non-financial-sector credit."""

from __future__ import annotations

import csv
import io
import math
import os
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from goldrush2.collectors.base import BaseCollector, SourceUnavailableError

BIS_URL = "https://api.bis.org/public/sdmx/v1/data/WS_TC(2.0)/Q.5A.P.A.M.USD.A?format=csv"
SERIES_KEY = "Q.5A.P.A.M.USD.A"
STALE_DAYS = 270


def quarter_end(period: str) -> str:
    try:
        year, quarter = period.strip().split("-Q")
        year_number, quarter_number = int(year), int(quarter)
        if quarter_number not in range(1, 5):
            raise ValueError
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid quarterly period: {period}") from exc
    month = quarter_number * 3
    day = 31 if month in (3, 12) else 30
    return date(year_number, month, day).isoformat()


def _value(row: dict[str, str]) -> str:
    return row.get("VALUE") or row.get("OBS_VALUE") or ""


def _matches(row: dict[str, str]) -> bool:
    expected = {
        "FREQ": "Q", "ADJUSTMENT": "A", "BORROWERS_CTY": "5A",
        "TC_BORROWERS": "P", "TC_LENDERS": "A", "VALUATION": "M",
        "UNIT_TYPE": "USD", "UNIT": "USD", "UNIT_MULT": "9", "TC_ADJUST": "A",
    }
    for key, wanted in expected.items():
        if key in row and row[key] and row[key] != wanted:
            return False
    return True


def parse_csv(data: bytes) -> list[dict[str, Any]]:
    try:
        text = data.decode("utf-8-sig")
        rows = csv.DictReader(io.StringIO(text))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError("BIS response is not valid CSV") from exc
    if not rows.fieldnames or "TIME_PERIOD" not in rows.fieldnames or not ({"VALUE", "OBS_VALUE"} & set(rows.fieldnames)):
        raise ValueError("BIS response does not contain TIME_PERIOD and VALUE columns")
    values: dict[str, float] = {}
    for row in rows:
        if not _matches(row):
            continue
        period = (row.get("TIME_PERIOD") or "").strip()
        if not period:
            continue
        observed = quarter_end(period)
        raw = _value(row).strip()
        if raw in {"", ".", "NA", "N/A"}:
            continue
        try:
            value = float(raw)
        except ValueError as exc:
            raise ValueError(f"invalid BIS credit value for {period}") from exc
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"BIS credit level must be positive for {period}")
        if observed in values and values[observed] != value:
            raise ValueError(f"conflicting duplicate BIS period: {period}")
        values[observed] = value
    if not values:
        raise ValueError("no BIS private non-financial-sector observations found")
    return [{"date": key, "value": values[key]} for key in sorted(values)]


class BISCollector(BaseCollector):
    """Fetch and cache the approved BIS quarterly credit series."""

    def __init__(self, cache_dir: Path, raw_path: Path, *, url: str = BIS_URL, force: bool = False, always_refresh: bool = False) -> None:
        super().__init__(cache_dir, force=force, always_refresh=always_refresh)
        self.raw_path = Path(raw_path)
        self.url = url

    @property
    def cache_path(self) -> Path:
        return self.cache_dir / "L7-003.json"

    @property
    def meta_path(self) -> Path:
        return self.cache_dir / "L7-003_meta.json"

    def _fetch(self) -> bytes:
        try:
            with urlopen(Request(self.url, headers={"Accept": "text/csv", "User-Agent": "GoldRush2 BIS collector"}), timeout=60) as response:
                data = response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise SourceUnavailableError(f"BIS request failed: {exc}") from exc
        if not data:
            raise SourceUnavailableError("BIS response was empty")
        return data

    def fetch_latest_observation_date(self) -> str:
        try:
            return max(row["date"] for row in parse_csv(self._fetch()))
        except (ValueError, SourceUnavailableError) as exc:
            raise SourceUnavailableError(str(exc)) from exc

    def download_full(self) -> list[dict[str, Any]]:
        data = self._fetch()
        try:
            rows = parse_csv(data)
        except ValueError as exc:
            raise SourceUnavailableError(str(exc)) from exc
        self.raw_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.raw_path.with_suffix(self.raw_path.suffix + ".tmp")
        temporary.write_bytes(data)
        os.replace(temporary, self.raw_path)
        return rows

    def download_incremental(self, since_date: str) -> list[dict[str, Any]]:
        raise NotImplementedError("BIS does not support incremental downloads")
