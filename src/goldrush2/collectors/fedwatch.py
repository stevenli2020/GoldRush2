"""CME FedWatch probability collector."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.collectors.base import BaseCollector, SourceUnavailableError


class FedWatchCollector(BaseCollector):
    handles_vars = ["L3-004"]
    SOURCE_NAME = "CME FedWatch - Policy Outcome Probabilities"
    SOURCE_URL = "https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html"
    CACHE_PATH = Path("data/cache/fedwatch/l3_004.json")
    RAW_PATH = Path("data/raw/fedwatch/probabilities.json")

    def __init__(self, cache_dir: Path, raw_dir: Path, **kwargs: Any) -> None:
        super().__init__(cache_dir, **kwargs)
        self._fedwatch_cache_path = Path(cache_dir) / "l3_004.json"
        self.raw_path = Path(raw_dir) / "fedwatch" / "probabilities.json"

    @property
    def cache_path(self) -> Path:
        return self._fedwatch_cache_path

    @staticmethod
    def _lower_bound(label: str) -> float | None:
        try:
            return float(label.split("%-", 1)[0].replace("%", ""))
        except (AttributeError, ValueError):
            return None

    @classmethod
    def _cut_probability(cls, probabilities: dict[str, Any], current_target: str) -> float:
        current = cls._lower_bound(current_target)
        if current is None:
            return 0.0
        return round(sum(float(value) for label, value in probabilities.items() if (cls._lower_bound(label) is not None and cls._lower_bound(label) < current)), 4)

    @classmethod
    def _normalize(cls, payload: dict[str, Any]) -> list[dict[str, Any]]:
        current_target = str(payload.get("current_target", ""))
        rows = []
        for item in payload.get("history", []):
            probabilities = item.get("probabilities", {})
            if isinstance(probabilities, dict):
                rows.append({"date": item["trade_date"], "cut_probability": cls._cut_probability(probabilities, current_target), "meeting_date": payload.get("meeting_date"), "contract": payload.get("contract")})
        return sorted({row["date"]: row for row in rows}.values(), key=lambda row: row["date"])

    def _fetch(self) -> dict[str, Any]:
        try:
            from cme_fedwatch import get_history
            return get_history(meeting="next", days=260)
        except Exception as exc:
            raise SourceUnavailableError(f"CME FedWatch request failed: {exc}") from exc

    def fetch(self, force: bool = False) -> Path:
        self.force = force
        if self.cache_path.exists() and not force:
            self.action = "cache"
            return self.cache_path
        try:
            raw = self._fetch()
            normalized = self._normalize(raw)
            if not normalized:
                raise SourceUnavailableError("CME FedWatch returned no probability history")
            self.raw_path.parent.mkdir(parents=True, exist_ok=True)
            self._atomic_json(self.raw_path, raw)
            self._atomic_json(self.cache_path, normalized)
            self.action = "full"
            return self.cache_path
        except SourceUnavailableError:
            if self.cache_path.exists():
                self.action = "cache"
                self.warning = "SOURCE UNAVAILABLE — cached data used"
                return self.cache_path
            raise

    def run(self) -> list[dict[str, Any]]:
        return json.loads(self.fetch(self.force).read_text(encoding="utf-8"))

    def fetch_latest_observation_date(self) -> str:
        rows = self.run()
        return rows[-1]["date"]

    def download_full(self) -> list[dict[str, Any]]:
        return self.run()
