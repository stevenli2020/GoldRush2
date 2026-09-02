"""Federal Reserve SEP HTML collector for L3-005."""

from __future__ import annotations

import io
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

from goldrush2.collectors.base import BaseCollector, SourceUnavailableError

SEP_CALENDAR_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
SNAPSHOT_PATH = Path("data/raw/L3-005_snapshot.html")


def _release_date(url: str) -> str:
    match = re.search(r"fomcprojtabl(\d{8})\.htm", url)
    if not match:
        raise ValueError(f"SEP URL has no release date: {url}")
    return datetime.strptime(match.group(1), "%Y%m%d").date().isoformat()


def candidate_urls(now: date | None = None) -> list[str]:
    """Return known SEP links from the calendar, plus conservative fallbacks."""
    today = now or date.today()
    urls: list[str] = []
    try:
        with urlopen(Request(SEP_CALENDAR_URL, headers={"User-Agent": "GoldRush2 Fed collector"}), timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")
        urls.extend("https://www.federalreserve.gov/monetarypolicy/" + match for match in re.findall(r"(?:href=[\"']?[^\"'>]*/)?(fomcprojtabl\d{8}\.htm)", html, re.I))
    except (HTTPError, URLError, TimeoutError, OSError):
        pass
    for year in range(today.year, today.year - 3, -1):
        for month in (12, 9, 6, 3):
            for day in (20, 18, 17, 16, 15, 14, 13, 12, 11, 10):
                urls.append(f"https://www.federalreserve.gov/monetarypolicy/fomcprojtabl{year:04d}{month:02d}{day:02d}.htm")
    return list(dict.fromkeys(urls))


def _numeric(value: Any) -> float | None:
    text = str(value).replace("%", "").replace("*", "").strip()
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None
    return number if pd.notna(number) else None


def parse_sep_html(content: bytes, release_date: str, source_url: str) -> dict[str, Any]:
    """Extract the median projection for the calendar year after release."""
    try:
        tables = pd.read_html(io.BytesIO(content))
    except ImportError:
        # The minimal GR2 environment may omit pandas' optional HTML engines;
        # BeautifulSoup provides the same small table extraction needed here.
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            tables = []
            for node in soup.find_all("table"):
                tables.append(pd.DataFrame([[cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])] for row in node.find_all("tr")]))
        except Exception as exc:
            raise ValueError("Federal Reserve SEP HTML contains no readable tables") from exc
    except ValueError as exc:
        raise ValueError("Federal Reserve SEP HTML contains no readable tables") from exc
    target_year = str(date.fromisoformat(release_date).year + 1)
    for table in tables:
        frame = table.copy()
        if len(frame) > 0 and all(str(column).isdigit() for column in frame.columns):
            frame.columns = [str(value).strip() for value in frame.iloc[0].tolist()]
            frame = frame.iloc[1:].reset_index(drop=True)
        frame.columns = [" ".join(str(part) for part in column if str(part) != "nan").strip() if isinstance(column, tuple) else str(column).strip() for column in frame.columns]
        for _, row in frame.iterrows():
            labels = " ".join(str(value).strip() for value in row.tolist()[:2])
            if "median" not in labels.lower():
                continue
            for column, value in row.items():
                if target_year in str(column):
                    numeric = _numeric(value)
                    if numeric is not None:
                        return {"date": release_date, "value": numeric, "source_url": source_url}
    raise ValueError(f"SEP median projection for {target_year} was not found")


class FedCollector(BaseCollector):
    handles_vars = ["L3-005"]

    def __init__(self, cache_dir: Path, raw_path: Path | None = None, *, force: bool = False, always_refresh: bool = False, snapshot_path: Path = SNAPSHOT_PATH) -> None:
        super().__init__(cache_dir, force=force, always_refresh=always_refresh)
        self.raw_path = Path(raw_path or "data/raw/L3-005.html")
        self.snapshot_path = Path(snapshot_path)
        self._pending: dict[str, Any] | None = None

    @property
    def cache_path(self) -> Path:
        return self.cache_dir / "L3-005.json"

    @property
    def meta_path(self) -> Path:
        return self.cache_dir / "L3-005_meta.json"

    def _fetch_latest(self) -> dict[str, Any]:
        for url in candidate_urls():
            try:
                with urlopen(Request(url, headers={"User-Agent": "GoldRush2 Fed collector"}), timeout=30) as response:
                    content = response.read()
                release = _release_date(url)
                record = parse_sep_html(content, release, url)
                self.raw_path.parent.mkdir(parents=True, exist_ok=True)
                temporary = self.raw_path.with_suffix(self.raw_path.suffix + ".tmp")
                temporary.write_bytes(content)
                temporary.replace(self.raw_path)
                return record
            except (HTTPError, URLError, TimeoutError, OSError, ValueError):
                continue
        if self.snapshot_path.exists():
            content = self.snapshot_path.read_bytes()
            release = "2026-06-17"
            return parse_sep_html(content, release, "https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20260617.htm")
        raise SourceUnavailableError("Federal Reserve SEP source is unavailable")

    def fetch_latest_observation_date(self) -> str:
        try:
            self._pending = self._fetch_latest()
            return str(self._pending["date"])
        except (SourceUnavailableError, ValueError) as exc:
            raise SourceUnavailableError(str(exc)) from exc

    def download_full(self) -> list[dict[str, Any]]:
        if self._pending is not None:
            record, self._pending = self._pending, None
        else:
            record = self._fetch_latest()
        # SEP releases are discrete; retain prior releases when BaseCollector
        # performs its full-download fallback so historical lag comparisons remain possible.
        return [*self.load_cache(), record]

    def download_incremental(self, since_date: str) -> list[dict[str, Any]]:
        raise NotImplementedError("SEP releases are discrete; use a full release fetch")
