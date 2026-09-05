"""CME FedWatch CSV collector with calendar-day forward filling."""

from __future__ import annotations

import csv
import json
import os
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from goldrush2.dr2.collectors.base import BaseCollector, SourceUnavailableError

from goldrush2.paths import DR2_ROOT as PROJECT_ROOT


class FedWatchCollector(BaseCollector):
    handles_vars = ["L3-004"]
    SOURCE_NAME = "CME FedWatch"
    SOURCE_URL = "https://www.cmegroup.com/markets/interest-rates/cme-fedwatch.html"
    DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "raw" / "fedwatch" / "FedMeeting_20260916.csv"
    CACHE_PATH = PROJECT_ROOT / "data/cache/fedwatch/l3_004.json"
    RAW_PATH = PROJECT_ROOT / "data/raw/fedwatch/probabilities.json"
    CURRENT_TARGET_LOWER_BPS = 350

    def __init__(self, cache_dir: Path, raw_dir: Path, **kwargs: Any) -> None:
        super().__init__(cache_dir, **kwargs)
        self._fedwatch_cache_path = Path(cache_dir) / "l3_004.json"
        self.raw_path = Path(raw_dir) / "fedwatch" / "probabilities.json"
        self.csv_path = Path(os.getenv("CME_FEDWATCH_CSV", self.DEFAULT_CSV_PATH))

    @property
    def cache_path(self) -> Path:
        return self._fedwatch_cache_path

    @staticmethod
    def _parse_date(value: str) -> date:
        for pattern in ("%Y-%m-%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(value.strip(), pattern).date()
            except ValueError:
                continue
        raise ValueError(f"Invalid FedWatch date: {value}")

    @staticmethod
    def _band_lower(header: str) -> float | None:
        match = re.search(r"\(?\s*(-?\d+(?:\.\d+)?)\s*(?:-|to)\s*", header)
        if match:
            return float(match.group(1))
        match = re.fullmatch(r"\s*\(?\s*(-?\d+(?:\.\d+)?)\s*\)?\s*", header)
        return float(match.group(1)) if match else None

    @classmethod
    def _is_easing_field(cls, header: str) -> bool:
        lower = cls._band_lower(header)
        if lower is None:
            return False
        if re.search(r"-|\bto\b", header) and not re.fullmatch(r"\s*\(?\s*-?\d+(?:\.\d+)?\s*\)?\s*", header):
            return lower < cls.CURRENT_TARGET_LOWER_BPS
        return lower < 0

    @classmethod
    def parse_csv(cls, path: Path, meeting_date: date | None = None) -> list[dict[str, Any]]:
        try:
            with path.open(newline="", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames or "Date" not in reader.fieldnames:
                    raise ValueError("FedWatch CSV has no Date column")
                band_fields = [(field, cls._band_lower(field)) for field in reader.fieldnames if field != "Date"]
                band_fields = [(field, lower) for field, lower in band_fields if lower is not None]
                if not band_fields:
                    raise ValueError("FedWatch CSV has no probability-band columns")
                rows = []
                for record in reader:
                    observed = cls._parse_date(record["Date"])
                    easing = 0.0
                    for field, _lower in band_fields:
                        raw = (record.get(field) or "").strip()
                        if raw and cls._is_easing_field(field):
                            easing += float(raw)
                    rows.append({"date": observed.isoformat(), "easing_prob": round(easing * (100 if easing <= 1 else 1), 6), "is_filled": False})
        except (OSError, csv.Error, KeyError, TypeError, ValueError) as exc:
            raise SourceUnavailableError(f"Cannot parse FedWatch CSV {path}: {exc}") from exc
        if not rows:
            raise SourceUnavailableError(f"FedWatch CSV {path} contained no observations")
        if meeting_date is not None and meeting_date > date.fromisoformat(rows[-1]["date"]):
            rows.append({"date": meeting_date.isoformat(), "easing_prob": rows[-1]["easing_prob"], "is_filled": True, "filled_from": rows[-1]["date"]})
        result = cls.forward_fill_dates(rows)
        if meeting_date is not None:
            for row in result:
                row["meeting_date"] = meeting_date.isoformat()
        return result

    def _load_csv_data(self, csv_path: Path | None = None) -> list[dict[str, Any]]:
        path = csv_path or self.csv_path
        meeting_date = self._meeting_date() if path == self.csv_path else None
        return self.parse_csv(path, meeting_date)

    @staticmethod
    def _forward_fill(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return FedWatchCollector.forward_fill_dates(observations)

    @staticmethod
    def forward_fill_dates(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        observations = sorted(observations, key=lambda row: row["date"])
        start = date.fromisoformat(observations[0]["date"])
        end = date.fromisoformat(observations[-1]["date"])
        lookup = {row["date"]: row for row in observations}
        filled: list[dict[str, Any]] = []
        last_value: float | None = None
        last_date: str | None = None
        current = start
        while current <= end:
            key = current.isoformat()
            if key in lookup:
                row = {"date": key, "easing_prob": lookup[key]["easing_prob"], "is_filled": bool(lookup[key].get("is_filled", False))}
                if row["is_filled"]:
                    row["filled_from"] = lookup[key].get("filled_from", last_date)
                last_value, last_date = row["easing_prob"], key
            else:
                row = {"date": key, "easing_prob": last_value, "is_filled": True, "filled_from": last_date}
            if row["easing_prob"] is not None:
                filled.append(row)
            current += timedelta(days=1)
        return filled

    def _meeting_date(self) -> date:
        match = re.search(r"(\d{8})", self.csv_path.name)
        if not match:
            raise SourceUnavailableError(f"Cannot determine meeting date from {self.csv_path.name}")
        return datetime.strptime(match.group(1), "%Y%m%d").date()

    @staticmethod
    def _safe_merge(existing: list[dict[str, Any]], new: list[dict[str, Any]], force: bool = False) -> list[dict[str, Any]]:
        """Preserve existing dates unless an explicit force replacement is requested."""
        if force:
            by_date = {row["date"]: row for row in new}
        else:
            by_date = {row["date"]: row for row in existing}
            for row in new:
                by_date.setdefault(row["date"], row)
        return [by_date[key] for key in sorted(by_date)]

    def _load_existing(self) -> list[dict[str, Any]]:
        if not self.cache_path.exists():
            return []
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SourceUnavailableError(f"Cannot read FedWatch cache {self.cache_path}: {exc}") from exc
        if not isinstance(payload, list) or not all(isinstance(row, dict) and "date" in row for row in payload):
            raise SourceUnavailableError(f"FedWatch cache {self.cache_path} must be a list of dated objects")
        return payload

    def fetch(self, force: bool = False) -> Path:
        self.force = force
        existing = self._load_existing()
        if force and self.cache_path.exists():
            backup_dir = self.cache_path.parent / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = backup_dir / f"{self.cache_path.stem}_{stamp}{self.cache_path.suffix}"
            backup.write_bytes(self.cache_path.read_bytes())
            self._log(f"WARNING: forced refresh backup created: {backup}", 1)
        if existing and not force:
            age = datetime.now(timezone.utc).timestamp() - self.cache_path.stat().st_mtime
            if age < 7 * 86400:
                self.action = "cache"
                self._log(f"FedWatch CSV cache reused: {self.cache_path}", 2)
                return self.cache_path
        try:
            meeting_date = self._meeting_date()
            incoming = self._load_csv_data()
            rows = self._safe_merge(existing, incoming, force=False)
            if not rows:
                raise SourceUnavailableError("FedWatch CSV produced no observations")
            self._atomic_json(self.cache_path, rows)
            self._atomic_json(self.raw_path, {"source_csv": str(self.csv_path), "meeting_date": meeting_date.isoformat(), "observations": incoming})
            previous = self.load_meta()
            refreshed_at = self._now() if force else previous.get("force_refreshed_at")
            self.save_meta({"last_observation_date": rows[-1]["date"], "downloaded_at": self._now(), "source_etag": previous.get("source_etag"), "force_refreshed_at": refreshed_at})
            self.action = "full"
            self._log(f"FedWatch CSV merged: source={self.csv_path} added={len(rows) - len(existing)} total={len(rows)} latest={rows[-1]['date']}", 1)
            return self.cache_path
        except SourceUnavailableError:
            if existing:
                self.action = "cache"
                self.warning = "SOURCE UNAVAILABLE — cached data used"
                return self.cache_path
            raise

    def run(self) -> list[dict[str, Any]]:
        return json.loads(self.fetch(self.force).read_text(encoding="utf-8"))

    def fetch_latest_observation_date(self) -> str:
        return self.run()[-1]["date"]

    def download_full(self) -> list[dict[str, Any]]:
        return self.run()
