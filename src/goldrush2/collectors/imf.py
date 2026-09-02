"""IMF COFER SDMX collector for the global USD reserve share."""

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

IMF_URL = "https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.STA/COFER/+/*?startPeriod=2000-Q1"
STALE_DAYS = 200


def quarter_end(period: str) -> str:
    try:
        year, quarter = period.strip().split("-Q")
        year_number, quarter_number = int(year), int(quarter)
        if quarter_number not in range(1, 5):
            raise ValueError
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid quarterly period: {period}") from exc
    month = quarter_number * 3
    return date(year_number, month, 31 if month in (3, 12) else 30).isoformat()


def _matches(row: dict[str, str]) -> bool:
    expected = {
        "COUNTRY": "G001", "INDICATOR": "AFXRA", "FXR_CURRENCY": "CI_USD",
        "TYPE_OF_TRANSFORMATION": "SHRO_PT", "FREQUENCY": "Q",
    }
    for key, wanted in expected.items():
        if key in row and row[key] and row[key] != wanted:
            return False
    return True


def parse_csv(data: bytes) -> list[dict[str, Any]]:
    try:
        reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError("IMF COFER response is not valid CSV") from exc
    if not reader.fieldnames or "TIME_PERIOD" not in reader.fieldnames or "OBS_VALUE" not in reader.fieldnames:
        raise ValueError("IMF COFER response does not contain expected columns")
    values: dict[str, float] = {}
    for row in reader:
        if row.get("STRUCTURE_ID") and not row["STRUCTURE_ID"].startswith("IMF.STA:COFER"):
            raise ValueError("unexpected IMF COFER structure identifier")
        if not _matches(row):
            continue
        period = (row.get("TIME_PERIOD") or "").strip()
        raw = (row.get("OBS_VALUE") or "").strip()
        if not period or raw in {"", ".", "NA", "N/A"}:
            continue
        observed = quarter_end(period)
        try:
            value = float(raw)
        except ValueError as exc:
            raise ValueError(f"invalid IMF COFER share for {period}") from exc
        if not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError(f"IMF COFER USD share must be between 0 and 100 for {period}")
        if observed in values and values[observed] != value:
            raise ValueError(f"conflicting duplicate IMF COFER period: {period}")
        values[observed] = value
    if not values:
        raise ValueError("no IMF COFER world USD-share observations found")
    return [{"date": key, "value": values[key]} for key in sorted(values)]


class IMFCollector(BaseCollector):
    """Fetch and cache IMF COFER world USD-share observations."""

    def __init__(self, cache_dir: Path, raw_path: Path, *, url: str = IMF_URL, force: bool = False, always_refresh: bool = False) -> None:
        super().__init__(cache_dir, force=force, always_refresh=always_refresh)
        self.raw_path = Path(raw_path)
        self.url = url

    @property
    def cache_path(self) -> Path:
        return self.cache_dir / "L5-003.json"

    @property
    def meta_path(self) -> Path:
        return self.cache_dir / "L5-003_meta.json"

    def _fetch(self) -> bytes:
        try:
            with urlopen(Request(self.url, headers={"Accept": "text/csv", "User-Agent": "GoldRush2 IMF collector"}), timeout=60) as response:
                data = response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise SourceUnavailableError(f"IMF COFER request failed: {exc}") from exc
        if not data:
            raise SourceUnavailableError("IMF COFER response was empty")
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
        raise NotImplementedError("IMF COFER incremental downloads are not enabled")
