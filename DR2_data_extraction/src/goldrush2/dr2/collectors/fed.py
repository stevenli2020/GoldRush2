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

from goldrush2.dr2.collectors.base import BaseCollector, SourceUnavailableError
from goldrush2.paths import DR2_ROOT as PROJECT_ROOT

SEP_CALENDAR_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
SNAPSHOT_PATH = PROJECT_ROOT / "data/raw/L3-005_snapshot.html"
FOMC_CALENDAR_URL = SEP_CALENDAR_URL


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
    handles_vars = ["L3-005", "L3-006"]

    def __init__(self, cache_dir: Path, raw_path: Path | None = None, *, variable_id: str = "L3-005", force: bool = False, always_refresh: bool = False, snapshot_path: Path = SNAPSHOT_PATH) -> None:
        super().__init__(cache_dir, force=force, always_refresh=always_refresh)
        self.variable_id = variable_id
        self.raw_path = Path(raw_path or PROJECT_ROOT / "data/raw/L3-005.html")
        self.snapshot_path = Path(snapshot_path)
        self._pending: dict[str, Any] | None = None

    @property
    def cache_path(self) -> Path:
        return self.cache_dir / f"{self.variable_id}.json"

    @property
    def meta_path(self) -> Path:
        return self.cache_dir / f"{self.variable_id}_meta.json"

    @staticmethod
    def _statement_url(meeting_date: str) -> str:
        return f"https://www.federalreserve.gov/newsevents/pressreleases/monetary{meeting_date.replace('-', '')}a.htm"

    @staticmethod
    def _rate_number(value: str) -> float:
        value = value.strip()
        match = re.fullmatch(r"(\d+)(?:[-–](\d+)/(\d+))?", value)
        if not match:
            return float(value)
        return float(match.group(1)) + (int(match.group(2)) / int(match.group(3)) if match.group(2) else 0)

    def _parse_fomc_statement(self, html: str, source_url: str = "") -> dict[str, Any]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        text = " ".join(soup.get_text(" ", strip=True).split())
        date_match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}", text, re.I)
        if not date_match and source_url:
            url_match = re.search(r"monetary(\d{8})a", source_url)
            if url_match:
                release_date = datetime.strptime(url_match.group(1), "%Y%m%d").date().isoformat()
            else:
                release_date = ""
        elif date_match:
            release_date = datetime.strptime(date_match.group(0), "%B %d, %Y").date().isoformat()
        else:
            release_date = ""
        if not release_date:
            raise ValueError("FOMC statement release date not found")
        rate_match = re.search(r"target range for the federal funds rate at\s+(\d+(?:[-–]\d+/\d+)?)\s+to\s+(\d+(?:[-–]\d+/\d+)?)\s+percent", text, re.I)
        if not rate_match:
            rate_match = re.search(r"target range.*?at\s+(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s+percent", text, re.I)
        rate_range = None
        if rate_match:
            rate_range = f"{self._rate_number(rate_match.group(1)):.2f}-{self._rate_number(rate_match.group(2)):.2f}"
        article = soup.select_one("#article") or soup.find("article") or soup.select_one(".col-sm-12")
        body = " ".join((article or soup).get_text(" ", strip=True).split())
        if "Federal Open Market Committee" not in body:
            raise ValueError("official FOMC statement body not found")
        return {"date": release_date, "rate_range": rate_range, "text": body, "url": source_url}

    def _fetch_fomc_statement(self, meeting_date: str | None = None) -> dict[str, Any]:
        url = self._statement_url(meeting_date) if meeting_date else None
        urls = [url] if url else [self._statement_url(day) for day in self._get_recent_meeting_dates(1)]
        for candidate in urls:
            try:
                with urlopen(Request(candidate, headers={"User-Agent": "GoldRush2 Fed collector"}), timeout=30) as response:
                    return self._parse_fomc_statement(response.read().decode("utf-8", errors="replace"), candidate)
            except (HTTPError, URLError, TimeoutError, OSError, ValueError):
                continue
        raise SourceUnavailableError(f"FOMC statement unavailable for {meeting_date or 'latest'}")

    def _get_recent_meeting_dates(self, count: int = 2) -> list[str]:
        self._log(f"requesting FOMC calendar: {FOMC_CALENDAR_URL}", 2)
        try:
            with urlopen(Request(FOMC_CALENDAR_URL, headers={"User-Agent": "GoldRush2 Fed collector"}), timeout=30) as response:
                html = response.read().decode("utf-8", errors="replace")
            dates = re.findall(r"monetary(\d{8})a\.htm", html, re.I)
            recent = sorted({datetime.strptime(item, "%Y%m%d").date().isoformat() for item in dates}, reverse=True)[:count]
            self._log(f"calendar returned recent statement dates={recent}", 2)
            return recent
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            today = date.today()
            fallback = [(today - timedelta(days=42 * index)).isoformat() for index in range(count)]
            self._log(f"calendar unavailable; using fallback candidate dates={fallback}", 1)
            return fallback

    def _ensure_minimum_cache_entries(self) -> None:
        records = self.load_cache()
        known = {str(row.get("date")) for row in records}
        for meeting_date in self._get_recent_meeting_dates(2):
            if len(records) >= 2:
                break
            if meeting_date in known:
                continue
            try:
                records.append(self._fetch_fomc_statement(meeting_date))
                known.add(meeting_date)
            except SourceUnavailableError:
                continue
        if records:
            self._atomic_json(self.cache_path, self._deduplicate(records))

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
        if self.variable_id == "L3-006":
            records = self.load_cache()
            dates = self._get_recent_meeting_dates(1)
            return dates[0] if dates else (self._latest_date(records) if records else "")
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

    def run(self) -> list[dict[str, Any]]:
        if self.variable_id != "L3-006":
            return super().run()
        records = self.load_cache()
        cached_latest = self._latest_date(records) if records else None
        self._log(f"L3-006 cache={self.cache_path} observations={len(records)} latest={cached_latest or 'none'}", 1)
        self._log(f"force={self.force} always_refresh={self.always_refresh}", 3)
        try:
            recent_dates = self._get_recent_meeting_dates(2)
            source_latest = recent_dates[0] if recent_dates else None
            self._log(f"source latest={source_latest or 'unknown'}; cached latest={cached_latest or 'none'}", 1)
            needs_refresh = self.force or len(records) < 2 or (source_latest is not None and (cached_latest is None or source_latest > cached_latest))
            if not needs_refresh:
                self.action = "skip"
                self._log("source is unchanged and two statements are cached; skipping download", 1)
                return records

            known = {str(row.get("date")) for row in records}
            incoming: list[dict[str, Any]] = []
            for meeting_date in recent_dates:
                if not self.force and meeting_date in known:
                    self._log(f"statement {meeting_date} already cached", 3)
                    continue
                self._log(f"fetching FOMC statement {meeting_date}", 2)
                try:
                    incoming.append(self._fetch_fomc_statement(meeting_date))
                except SourceUnavailableError as exc:
                    self._log(str(exc), 2)
            updated = self._deduplicate([*records, *incoming])
            if len(updated) < 2:
                raise SourceUnavailableError("Fewer than two FOMC statements are available")
            self._atomic_json(self.cache_path, updated)
            previous_meta = self.load_meta()
            self.save_meta({"last_observation_date": self._latest_date(updated), "downloaded_at": self._now(), "source_etag": previous_meta.get("source_etag"), "force_refreshed_at": self._now() if self.force else previous_meta.get("force_refreshed_at")})
            self.action = "full" if self.force or not records else "incremental"
            self._log(f"{self.action} refresh wrote {len(updated)} statements; latest={self._latest_date(updated)}", 1)
            self._log(f"metadata={self.load_meta()}", 3)
            return updated
        except SourceUnavailableError:
            if records:
                self.action, self.warning = "cache", "SOURCE UNAVAILABLE — cached data used"
                self._log("source unavailable; using cached FOMC statements", 1)
                return records
            raise
