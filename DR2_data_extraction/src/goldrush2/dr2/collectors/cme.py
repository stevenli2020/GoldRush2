"""Collection and parsing of the CME 30-Day Fed Funds futures bulletin."""

from __future__ import annotations

import json
import os
import re
import tempfile
import subprocess
from calendar import monthrange
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from goldrush2.dr2.collectors.base import BaseCollector, CollectorError
from goldrush2.paths import DR2_ROOT

CME_BULLETIN_URL = "https://www.cmegroup.com/daily_bulletin/Section10_Interest_Rate_Futures_Continued.pdf"
SOURCE_URL = CME_BULLETIN_URL
DEFAULT_RAW_PATH = DR2_ROOT / "data" / "raw" / "cme" / "Section10_Interest_Rate_Futures_Continued.pdf"
DEFAULT_MANIFEST_PATH = DEFAULT_RAW_PATH.with_name("manifest.json")
DEFAULT_ZQ_RAW_PATH = DEFAULT_RAW_PATH.with_name("ZQ=F_full.json")
DEFAULT_ZQ_CACHE_PATH = DR2_ROOT / "data" / "cache" / "L1-006.json"
DEFAULT_CURVE_RAW_PATH = DEFAULT_RAW_PATH.with_name("ZQ_curve_latest.json")
DEFAULT_CURVE_CACHE_PATH = DR2_ROOT / "data" / "cache" / "cme" / "L3-002.json"
ZQ_HISTORY_MAX_AGE_DAYS = 7
MONTH_CODES = {1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M", 7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"}
MONTHS = {name: number for number, name in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"), 1)}


class CmeError(CollectorError):
    """Base error for CME collection and parsing failures."""


class CmeNetworkError(CmeError):
    """Raised when the CME bulletin cannot be downloaded."""


class CmeDataError(CmeError):
    """Raised when the CME bulletin is not a usable PDF/table."""


def _write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def _load_rate_cache(path: Path) -> list[dict[str, str | float]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return []
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict) and row.get("date") and row.get("rate") is not None]


def _deduplicate_rate_rows(rows: list[dict[str, str | float]]) -> list[dict[str, str | float]]:
    by_date = {str(row["date"]): row for row in rows}
    return [by_date[key] for key in sorted(by_date)]


def normalize_zq_history(frame: object) -> list[dict[str, str | float]]:
    """Convert Yahoo's daily continuous ZQ contract into weekly implied rates."""
    try:
        import pandas as pd
    except ImportError as exc:
        raise CmeDataError("pandas is required to normalize ZQ history") from exc
    close = frame["Close"]  # type: ignore[index]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = pd.to_numeric(close, errors="coerce").dropna()
    if close.empty:
        raise CmeDataError("Yahoo ZQ history contained no closing prices")
    close.index = pd.to_datetime(close.index, utc=True).tz_localize(None)
    weekly = close.groupby(close.index.to_period("W-FRI")).last()
    rows = []
    for period, price in weekly.items():
        observation_date = close[close.index.to_period("W-FRI") == period].index.max().date().isoformat()
        rows.append({"date": observation_date, "rate": round(100.0 - float(price), 6)})
    return rows


def refresh_zq_history(*, force: bool = False, raw_path: Path = DEFAULT_ZQ_RAW_PATH, cache_path: Path = DEFAULT_ZQ_CACHE_PATH) -> list[dict[str, str | float]]:
    """Fetch Yahoo ZQ history on first use and refresh it at most every seven days."""
    if force and cache_path.exists():
        backup_dir = cache_path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = backup_dir / f"{cache_path.stem}_{stamp}{cache_path.suffix}"
        backup.write_bytes(cache_path.read_bytes())
    if cache_path.exists() and not force:
        age = max(0.0, datetime.now(timezone.utc).timestamp() - cache_path.stat().st_mtime)
        if age < ZQ_HISTORY_MAX_AGE_DAYS * 86400:
            return _load_rate_cache(cache_path)
    try:
        import yfinance as yf
        frame = yf.download("ZQ=F", period="max", interval="1d", auto_adjust=False, progress=False, threads=False)
        rows = normalize_zq_history(frame)
    except Exception as exc:
        existing = _load_rate_cache(cache_path)
        if existing:
            return existing
        raise CmeNetworkError(f"Yahoo ZQ history unavailable: {exc}") from exc
    raw_rows = [{"date": row["date"], "implied_rate": row["rate"]} for row in rows]
    _write_json_atomic(raw_path, raw_rows)
    if cache_path.exists():
        existing = _load_rate_cache(cache_path)
        rows = _deduplicate_rate_rows([*existing, *rows])
    _write_json_atomic(cache_path, rows)
    return rows


def month_end_business_day(year: int, month: int) -> date:
    """Return the last weekday of a contract month."""
    day = monthrange(year, month)[1]
    while date(year, month, day).weekday() >= 5:
        day -= 1
    return date(year, month, day)


def _contract(month_name: str, year_suffix: str) -> tuple[str, date]:
    month = MONTHS.get(month_name)
    if month is None:
        raise CmeDataError(f"Unknown CME contract month: {month_name}")
    year = 2000 + int(year_suffix)
    return f"ZQ{MONTH_CODES[month]}{year_suffix}", month_end_business_day(year, month)


def parse_fed_futures_text(text: str) -> list[dict[str, str | float]]:
    """Parse the 30D FED FD FUT table from extracted CME PDF text."""
    start = text.find("30D FED FD FUT")
    if start < 0:
        raise CmeDataError("30D FED FD FUT section not found")
    end = text.find("TOTAL", start)
    block = text[start:] if end < 0 else text[start:end]
    matches = list(re.finditer(r"\b([A-Z]{3})(\d{2})\b", block))
    settlement_pattern = re.compile(r"([0-9]{2,3}\.[0-9]{4})\s*\(")
    rows: list[dict[str, str | float]] = []
    for index, match in enumerate(matches):
        month_name, year_suffix = match.groups()
        if month_name not in MONTHS:
            continue
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        settlement = settlement_pattern.search(block[match.end():next_start])
        if settlement is None:
            continue
        contract, expiry = _contract(month_name, year_suffix)
        settlement_price = float(settlement.group(1))
        rows.append({"contract": contract, "settlement_price": settlement_price, "expiry_date": expiry.isoformat(), "implied_rate": 100 - settlement_price})
    if not rows:
        raise CmeDataError("no 30-Day Fed Funds settlement rows found")
    return rows


def parse_fed_futures_table(pdf_path: Path) -> list[dict[str, str | float]]:
    """Extract and parse the 30D FED FD FUT table from a PDF."""
    try:
        extracted = subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"], check=True, capture_output=True, text=True, timeout=60)
        return parse_fed_futures_text(extracted.stdout)
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass
    try:
        data = pdf_path.read_bytes()
    except OSError as exc:
        raise CmeDataError(f"cannot read CME PDF: {pdf_path}") from exc
    if b"%PDF" not in data[:1024]:
        raise CmeDataError("CME bulletin is not a PDF")
    try:
        from pypdf import PdfReader
        import io

        text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)
    except ImportError as exc:
        raise CmeDataError("pypdf is required to parse the CME bulletin") from exc
    except Exception as exc:
        raise CmeDataError("CME PDF text extraction failed") from exc
    return parse_fed_futures_text(text)


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    temporary.replace(path)


def fetch_cme_bulletin(*, raw_path: Path = DEFAULT_RAW_PATH, manifest_path: Path = DEFAULT_MANIFEST_PATH, timeout: float = 30) -> tuple[Path, dict[str, object]]:
    """Download, validate, cache, and describe the current CME Section 10 bulletin."""
    headers = {"User-Agent": "Mozilla/5.0 GoldRush2/0.1", "Referer": "https://www.cmegroup.com/market-data/daily-bulletin.html"}
    cookie_header = os.getenv("CME_COOKIES")
    if cookie_header:
        headers["Cookie"] = cookie_header
    request = Request(SOURCE_URL, headers=headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            content = response.read()
    except (HTTPError, URLError, OSError) as exc:
        raise CmeNetworkError(f"CME bulletin unavailable: {exc}") from exc
    if b"%PDF" not in content[:1024]:
        raise CmeDataError("CME bulletin response is not a PDF")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = raw_path.with_suffix(raw_path.suffix + ".tmp")
    temporary_path.write_bytes(content)
    try:
        rows = parse_fed_futures_table(temporary_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    _write_atomic(raw_path, content)
    retrieved = datetime.now(timezone.utc)
    manifest: dict[str, object] = {"download_date": retrieved.date().isoformat(), "source_url": SOURCE_URL, "contracts_found": len(rows), "latest_observation_date": retrieved.date().isoformat(), "status": "AVAILABLE", "retrieved_at": retrieved.isoformat()}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return raw_path, manifest


class CMECurveCollector(BaseCollector):
    """Collect the current CME Fed Funds futures curve for L3-002/L3-003."""

    handles_vars = ["L3-002", "L3-003"]

    def __init__(self, cache_dir: Path, raw_path: Path, *, force: bool = False, always_refresh: bool = False, verbose: int = 0) -> None:
        super().__init__(cache_dir, force=force, always_refresh=always_refresh, verbose=verbose)
        self.raw_path = Path(raw_path)

    def fetch_latest_observation_date(self) -> str:
        return date.today().isoformat()

    @property
    def cache_path(self) -> Path:
        return self.cache_dir / "L3-002.json"

    def download_full(self) -> list[dict[str, str | float]]:
        return self._download_curve()

    def _download_curve(self) -> list[dict[str, str | float]]:
        local_candidates = sorted(self.raw_path.parent.glob("*-DLYBLLTN_DB_*.pdf"), key=lambda path: path.stat().st_mtime, reverse=True)
        local_candidates += sorted(self.raw_path.parent.glob("Section10_Interest_Rate_Futures_Continued*.pdf"), key=lambda path: path.stat().st_mtime, reverse=True)
        pdf_path = local_candidates[0] if local_candidates else None
        if pdf_path is not None:
            self._log(f"using authenticated local CME bulletin: {pdf_path.name}")
            match = re.match(r"(\d{8})-DLYBLLTN_DB_", pdf_path.name)
            observation_date = datetime.strptime(match.group(1), "%Y%m%d").date().isoformat() if match else date.today().isoformat()
        else:
            self._log("requesting CME Section 10 bulletin for current ZQ curve")
            pdf_path, manifest = fetch_cme_bulletin(raw_path=self.raw_path.with_suffix(".pdf"))
            observation_date = str(manifest["latest_observation_date"])
        rows = [row for row in parse_fed_futures_table(pdf_path) if str(row["expiry_date"]) > observation_date]
        if not rows:
            raise CmeDataError("no unexpired ZQ contracts found")
        _write_json_atomic(self.raw_path, {"observation_date": observation_date, "status": "AVAILABLE", "curve": rows})
        return [{"date": observation_date, **row} for row in rows]

    def run(self) -> list[dict[str, str | float]]:
        if self.cache_path.exists() and not self.force and not self.always_refresh:
            self.action = "skip"
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
            return [{"date": str(payload["observation_date"]), **row} for row in payload.get("curve", [])]
        try:
            rows = self._download_curve()
            observation_date = rows[0]["date"]
            payload = {"observation_date": observation_date, "status": "AVAILABLE", "curve": [{key: value for key, value in row.items() if key != "date"} for row in rows]}
            _write_json_atomic(self.cache_path, payload)
            self.save_meta({"last_observation_date": observation_date, "downloaded_at": self._now(), "source_etag": None, "force_refreshed_at": self._now() if self.force else None})
            self.action = "full"
            return rows
        except (CmeError, OSError, json.JSONDecodeError) as exc:
            if self.cache_path.exists():
                self.action = "cache"
                self.warning = f"SOURCE UNAVAILABLE — cached curve used: {exc}"
                payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
                observation_date = str(payload["observation_date"])
                return [{"date": observation_date, **row} for row in payload.get("curve", [])]
            raise CmeNetworkError(str(exc)) from exc
