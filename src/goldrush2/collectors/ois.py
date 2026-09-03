"""Free OIS curve collector: DTCC backfill plus CheckMySwap accumulation."""
from __future__ import annotations
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from goldrush2.collectors.base import BaseCollector, SourceUnavailableError

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CHECKMYSWAP_URL = "https://cadampog.com/temp/datafeed/"
DTCC_SEED_PATH = PROJECT_ROOT / "data" / "cache" / "dtcc" / "sofr_ois_curves_2y.json"

def _read_json(path: Path, default: Any) -> Any:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError): return default

def _checkmyswap_rows(payload: Any) -> list[dict[str, Any]]:
    result = []
    for record in payload.get("data", []) if isinstance(payload, dict) else []:
        if not isinstance(record, dict) or not isinstance(record.get("curve"), list): continue
        curve = []
        for point in record["curve"]:
            tenor = str(point.get("tenor", "")).upper() if isinstance(point, dict) else ""
            if not tenor.endswith("Y") or point.get("rate") is None: continue
            try: curve.append({"tenor": tenor, "rate": float(point["rate"]), "trade_count": point.get("trades")})
            except (TypeError, ValueError): continue
        if curve and isinstance(record.get("date"), str): result.append({"date": record["date"], "curve": curve, "source": "CheckMySwap"})
    return result

def _dtcc_seed() -> list[dict[str, Any]]:
    result = []
    for row in _read_json(DTCC_SEED_PATH, []) if isinstance(_read_json(DTCC_SEED_PATH, []), list) else []:
        curve = [{"tenor": f"{p['tenor_years']}Y", "rate": float(p["rate"]) * 100, "trade_count": p.get("trade_count")} for p in row.get("curve", []) if p.get("rate") is not None]
        if curve: result.append({"date": row["date"], "curve": curve, "source": "DTCC-derived"})
    return result

class OISCollector(BaseCollector):
    handles_vars = ["L3-002", "L3-003"]
    def __init__(self, cache_dir: Path, raw_path: Path, *, force=False, always_refresh=False, verbose=0):
        super().__init__(cache_dir, force=force, always_refresh=always_refresh, verbose=verbose); self.raw_path = Path(raw_path)
    @property
    def cache_path(self) -> Path: return self.cache_dir / "ois_curves.json"
    def _request(self, from_date: str) -> list[dict[str, Any]]:
        query = urlencode({"from": from_date.replace("-", "")}); self._log(f"request started: {CHECKMYSWAP_URL}?{query}", 1)
        try:
            with urlopen(Request(f"{CHECKMYSWAP_URL}?{query}", headers={"Accept":"application/json","User-Agent":"GoldRush2-OIS"}), timeout=30) as response: payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, OSError, json.JSONDecodeError) as exc: raise SourceUnavailableError(f"CheckMySwap request failed: {exc}") from exc
        rows = _checkmyswap_rows(payload); self._log(f"request completed: {len(rows)} curve observations", 1)
        if not rows: raise SourceUnavailableError("CheckMySwap returned no valid curve observations")
        self.raw_path.parent.mkdir(parents=True, exist_ok=True); self.raw_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8"); return rows
    def fetch_latest_observation_date(self) -> str: return self._request((date.today() - timedelta(days=7)).isoformat())[0]["date"]
    def download_full(self) -> list[dict[str, Any]]:
        seeded = _dtcc_seed(); return [*seeded, *self._request(seeded[0]["date"] if seeded else "2000-01-01")]
    def download_incremental(self, since_date: str) -> list[dict[str, Any]]: return self._request(since_date)
