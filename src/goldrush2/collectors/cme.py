"""Collection and parsing of the CME 30-Day Fed Funds futures bulletin."""

from __future__ import annotations

import json
import os
import re
import tempfile
from calendar import monthrange
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CME_BULLETIN_URL = "https://www.cmegroup.com/daily_bulletin/Section10_Interest_Rate_Futures_Continued.pdf"
SOURCE_URL = CME_BULLETIN_URL
DEFAULT_RAW_PATH = Path(__file__).resolve().parents[3] / "data" / "raw" / "cme" / "Section10_Interest_Rate_Futures_Continued.pdf"
DEFAULT_MANIFEST_PATH = DEFAULT_RAW_PATH.with_name("manifest.json")
MONTH_CODES = {1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M", 7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"}
MONTHS = {name: number for number, name in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"), 1)}


class CmeError(RuntimeError):
    """Base error for CME collection and parsing failures."""


class CmeNetworkError(CmeError):
    """Raised when the CME bulletin cannot be downloaded."""


class CmeDataError(CmeError):
    """Raised when the CME bulletin is not a usable PDF/table."""


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
