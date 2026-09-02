"""CFTC Disaggregated Futures-Only COT collector for L10-001 and L10-002."""

from __future__ import annotations

import csv
import io
import json
import os
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests

from goldrush2.collectors.base import BaseCollector, SourceUnavailableError


class CFTCCollector(BaseCollector):
    handles_vars = ["L10-001", "L10-002"]
    SOURCE_NAME = "CFTC Disaggregated COT Report"
    SOURCE_URL = "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"
    CURRENT_URL = "https://www.cftc.gov/dea/newcot/f_disagg.txt"
    HISTORY_URL_TEMPLATE = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{}.zip"
    GOLD_SYMBOL = "GOLD - COMMODITY EXCHANGE INC."
    STALE_THRESHOLD_DAYS = 10
    FIRST_YEAR = 2009

    def __init__(self, cache_root: Path, raw_dir: Path, **kwargs: Any) -> None:
        super().__init__(cache_root, **kwargs)
        self.raw_dir = Path(raw_dir) / "cftc"
        self.session = requests.Session()

    @property
    def l10_001_cache_path(self) -> Path:
        return self.cache_dir / "L10-001.json"

    @property
    def l10_002_cache_path(self) -> Path:
        return self.cache_dir / "L10-002.json"

    @property
    def l10_001_meta_path(self) -> Path:
        return self.cache_dir / "L10-001_meta.json"

    @property
    def l10_002_meta_path(self) -> Path:
        return self.cache_dir / "L10-002_meta.json"

    @staticmethod
    def _integer(value: str) -> int | None:
        value = value.strip().replace(",", "")
        if value in {"", ".", "-"}:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    @classmethod
    def _parse_row(cls, row: list[str]) -> dict[str, Any]:
        if len(row) < 15 or row[0].strip() != cls.GOLD_SYMBOL:
            raise ValueError("CFTC gold row not found")
        report_date = row[2].strip()
        datetime.strptime(report_date, "%Y-%m-%d")
        open_interest = cls._integer(row[7])
        managed_long = cls._integer(row[13])
        managed_short = cls._integer(row[14])
        if open_interest is None or managed_long is None or managed_short is None:
            raise ValueError("CFTC gold managed-money or open-interest field is missing")
        return {"date": report_date, "net": managed_long - managed_short, "open_interest": open_interest, "managed_money_long": managed_long, "managed_money_short": managed_short}

    @classmethod
    def _parse_report(cls, text: str) -> dict[str, Any]:
        for row in csv.reader(io.StringIO(text)):
            if row and row[0].strip() == cls.GOLD_SYMBOL:
                return cls._parse_row(row)
        raise ValueError(f"CFTC report does not contain {cls.GOLD_SYMBOL}")

    @classmethod
    def _parse_text_rows(cls, text: str) -> list[dict[str, Any]]:
        rows = []
        for row in csv.reader(io.StringIO(text)):
            if row and row[0].strip() == cls.GOLD_SYMBOL:
                try:
                    rows.append(cls._parse_row(row))
                except ValueError:
                    continue
        return rows

    def _get(self, url: str) -> requests.Response:
        try:
            response = self.session.get(url, timeout=60, headers={"User-Agent": "GoldRush2-CFTC"})
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"CFTC request failed: {exc}") from exc

    def _fetch_current_report(self) -> str:
        return self._get(self.CURRENT_URL).text

    def _fetch_historical_report(self, year: int) -> str:
        response = self._get(self.HISTORY_URL_TEMPLATE.format(year))
        try:
            with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                names = [name for name in archive.namelist() if not name.endswith("/")]
                if not names:
                    raise ValueError("archive is empty")
                return archive.read(names[0]).decode("utf-8-sig", errors="replace")
        except (zipfile.BadZipFile, KeyError, ValueError) as exc:
            raise SourceUnavailableError(f"CFTC {year} archive is invalid") from exc

    def _load_history(self) -> list[dict[str, Any]]:
        all_rows: list[dict[str, Any]] = []
        for year in range(self.FIRST_YEAR, date.today().year + 1):
            try:
                text = self._fetch_historical_report(year)
                year_rows = self._parse_text_rows(text)
                all_rows.extend(year_rows)
                self._log(f"historical {year}: {len(year_rows)} gold rows", 3)
            except SourceUnavailableError:
                self._log(f"historical {year}: unavailable", 3)
                continue
        by_date = {row["date"]: row for row in all_rows}
        return [by_date[key] for key in sorted(by_date)]

    def _save_both(self, rows: list[dict[str, Any]], *, force: bool = False) -> None:
        downloaded_at = self._now()
        latest = rows[-1]["date"]
        for path, meta_path, payload in ((self.l10_001_cache_path, self.l10_001_meta_path, [{"date": r["date"], "net": r["net"]} for r in rows]), (self.l10_002_cache_path, self.l10_002_meta_path, [{"date": r["date"], "open_interest": r["open_interest"]} for r in rows])):
            self._atomic_json(path, payload)
            self._atomic_json(meta_path, {"last_observation_date": latest, "downloaded_at": downloaded_at, "source_etag": None, "force_refreshed_at": downloaded_at if force else None})

    def _fresh(self, path: Path, meta_path: Path) -> bool:
        try:
            latest = json.loads(meta_path.read_text(encoding="utf-8"))["last_observation_date"]
            return path.exists() and (date.today() - date.fromisoformat(latest)).days < self.STALE_THRESHOLD_DAYS
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return False

    def fetch(self, force: bool = False) -> dict[str, Path]:
        if not force and self._fresh(self.l10_001_cache_path, self.l10_001_meta_path) and self._fresh(self.l10_002_cache_path, self.l10_002_meta_path):
            self.action = "cache"
            self._log("both L10 caches are fresh; skipping CFTC download", 1)
            return {"L10-001": self.l10_001_cache_path, "L10-002": self.l10_002_cache_path}
        self._log("requesting current CFTC gold report", 1)
        try:
            current = self._parse_report(self._fetch_current_report())
            self._log(f"current report date={current['date']}; loading historical reports", 2)
            rows = self._load_history()
            by_date = {row["date"]: row for row in rows}
            by_date[current["date"]] = current
            rows = [by_date[key] for key in sorted(by_date)]
            self._save_both(rows, force=force)
            self.action = "full"
            self._log(f"CFTC refresh wrote {len(rows)} observations; latest={rows[-1]['date']}", 1)
            return {"L10-001": self.l10_001_cache_path, "L10-002": self.l10_002_cache_path}
        except (SourceUnavailableError, ValueError):
            self._log("CFTC source unavailable; checking snapshot fallback", 1)
            snapshots = []
            for variable in ("L10-001", "L10-002"):
                snapshot = self.raw_dir / f"{variable}_snapshot.json"
                target = self.cache_dir / f"{variable}.json"
                if snapshot.exists():
                    self._atomic_json(target, json.loads(snapshot.read_text(encoding="utf-8")))
                    snapshots.append(target)
            if len(snapshots) == 2:
                self.action = "snapshot"
                self.warning = "SOURCE UNAVAILABLE — snapshots used"
                self._log("CFTC snapshot fallback loaded", 1)
                return {"L10-001": snapshots[0], "L10-002": snapshots[1]}
            raise

    def run(self) -> list[dict[str, Any]]:
        paths = self.fetch(self.force)
        return json.loads(paths["L10-002"].read_text(encoding="utf-8"))

    def fetch_latest_observation_date(self) -> str:
        return self._parse_report(self._fetch_current_report())["date"]

    def download_full(self) -> list[dict[str, Any]]:
        rows = self._load_history()
        if not rows:
            raise SourceUnavailableError("CFTC returned no historical gold observations")
        return rows
