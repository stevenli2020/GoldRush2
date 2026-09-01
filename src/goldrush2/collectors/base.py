"""Shared refresh orchestration for normalized collector caches."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CollectorError(RuntimeError):
    """Raised when a collector cannot produce a usable normalized cache."""


class SourceUnavailableError(CollectorError):
    """Raised when the remote source cannot be reached or parsed."""


class BaseCollector(ABC):
    """Refresh a per-variable normalized cache while preserving a raw source cache.

    Subclasses own source access and return records containing at least a
    ``date`` field.  This class owns the policy-independent cache lifecycle.
    """

    def __init__(self, cache_dir: Path, force: bool = False, always_refresh: bool = False) -> None:
        self.cache_dir = Path(cache_dir)
        self.force = force
        self.always_refresh = always_refresh
        self.action: str | None = None
        self.warning: str | None = None

    @property
    def cache_path(self) -> Path:
        return self.cache_dir / "observations.json"

    @property
    def meta_path(self) -> Path:
        return self.cache_dir / "_meta.json"

    @abstractmethod
    def fetch_latest_observation_date(self) -> str:
        """Return the newest source observation date in ISO format."""

    @abstractmethod
    def download_full(self) -> list[dict[str, Any]]:
        """Download and normalize the complete supported source history."""

    def download_incremental(self, since_date: str) -> list[dict[str, Any]]:
        """Download observations at or after ``since_date`` when supported."""
        raise NotImplementedError

    def load_meta(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.meta_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CollectorError(f"Cannot read collector metadata: {self.meta_path}") from exc
        if not isinstance(payload, dict):
            raise CollectorError("Collector metadata must be an object")
        return payload

    def save_meta(self, meta: dict[str, Any]) -> None:
        self._atomic_json(self.meta_path, meta)

    def load_cache(self) -> list[dict[str, Any]]:
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return []
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CollectorError(f"Cannot read normalized cache: {self.cache_path}") from exc
        if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
            raise CollectorError("Normalized cache must be a list of objects")
        return payload

    def _update_cache(self, existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged = self._deduplicate([*existing, *incoming])
        if not merged:
            raise CollectorError("Collector returned no valid observations")
        self._atomic_json(self.cache_path, merged)
        return merged

    def _deduplicate(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_date: dict[str, dict[str, Any]] = {}
        for row in rows:
            observation_date = row.get("date")
            if not isinstance(observation_date, str) or not observation_date:
                raise CollectorError("Every normalized observation requires a date")
            by_date[observation_date] = row
        return [by_date[key] for key in sorted(by_date)]

    def _atomic_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _latest_date(rows: list[dict[str, Any]]) -> str:
        return max(str(row["date"]) for row in rows)

    def _save_updated(self, existing: list[dict[str, Any]], incoming: list[dict[str, Any]], action: str) -> list[dict[str, Any]]:
        rows = self._update_cache(existing, incoming)
        previous = self.load_meta()
        meta = {
            "last_observation_date": self._latest_date(rows),
            "downloaded_at": self._now(),
            "source_etag": previous.get("source_etag"),
            "force_refreshed_at": self._now() if self.force else previous.get("force_refreshed_at"),
        }
        self.save_meta(meta)
        self.action = action
        return rows

    def run(self) -> list[dict[str, Any]]:
        """Apply force, source-date, incremental, and cache-fallback rules."""
        existing = self.load_cache()
        has_cache = self.cache_path.exists()
        meta = self.load_meta() if has_cache else {}
        last_date = meta.get("last_observation_date") or (self._latest_date(existing) if existing else None)

        if self.force or not has_cache:
            try:
                return self._save_updated([], self.download_full(), "full")
            except SourceUnavailableError:
                if has_cache:
                    self.action = "cache"
                    self.warning = "SOURCE UNAVAILABLE — cached data used"
                    return existing
                raise

        if self.always_refresh:
            try:
                return self._save_updated(existing, self.download_incremental(last_date or self._latest_date(existing)), "incremental")
            except (NotImplementedError, SourceUnavailableError):
                try:
                    return self._save_updated([], self.download_full(), "full")
                except SourceUnavailableError:
                    self.action = "cache"
                    self.warning = "SOURCE UNAVAILABLE — cached data used"
                    return existing

        try:
            source_date = self.fetch_latest_observation_date()
        except SourceUnavailableError:
            self.action = "cache"
            self.warning = "SOURCE UNAVAILABLE — cached data used"
            return existing

        if last_date is not None and source_date <= last_date:
            self.action = "skip"
            return existing

        try:
            return self._save_updated(existing, self.download_incremental(last_date or source_date), "incremental")
        except (NotImplementedError, SourceUnavailableError):
            try:
                return self._save_updated([], self.download_full(), "full")
            except SourceUnavailableError:
                self.action = "cache"
                self.warning = "SOURCE UNAVAILABLE — cached data used"
                return existing
