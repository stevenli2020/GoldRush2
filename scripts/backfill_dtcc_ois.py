"""Backfill dated DTCC CFTC rates files into a normalized OIS curve cache."""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import os
import tempfile
import zipfile
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "dtcc" / "cftc_rates"
OUT_PATH = ROOT / "data" / "cache" / "dtcc" / "sofr_ois_curves.json"
MANIFEST_PATH = ROOT / "data" / "cache" / "dtcc" / "sofr_ois_backfill_meta.json"
URL = "https://kgc0418-tdw-data-0.s3.amazonaws.com/cftc/eod/CFTC_CUMULATIVE_RATES_{date}.zip"
TENORS = (1, 2, 3, 5, 7, 10, 30)


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as f:
        json.dump(value, f, indent=2)
        f.write("\n")
        tmp = Path(f.name)
    os.replace(tmp, path)


def fetch_one(day: dt.date) -> tuple[str, bytes | None, int]:
    stamp = day.strftime("%Y_%m_%d")
    try:
        response = requests.get(URL.format(date=stamp), timeout=90)
        if response.status_code != 200:
            return stamp, None, response.status_code
        return stamp, response.content, 200
    except requests.RequestException:
        return stamp, None, 0


def parse_file(stamp: str, payload: bytes) -> dict:
    archive = zipfile.ZipFile(io.BytesIO(payload))
    csv_name = archive.namelist()[0]
    rows = csv.DictReader(io.TextIOWrapper(archive.open(csv_name), encoding="utf-8"))
    grouped: dict[int, list[tuple[float, float]]] = {tenor: [] for tenor in TENORS}
    filtered = 0
    for row in rows:
        if row.get("Notional currency-Leg 1") != "USD" or row.get("Event type") != "TRAD":
            continue
        if "SOFR" not in (row.get("UPI Underlier Name", "") + " " + row.get("UPI FISN", "")).upper():
            continue
        if "OIS" not in row.get("UPI FISN", "").upper():
            continue
        try:
            rate = float(row["Fixed rate-Leg 1"])
            effective = dt.date.fromisoformat(row["Effective Date"])
            expiry = dt.date.fromisoformat(row["Expiration Date"])
            notional = float(row["Notional amount-Leg 1"].replace(",", ""))
            years = (expiry - effective).days / 365.25
            tenor = min(TENORS, key=lambda value: abs(value - years))
            if rate >= 0 and notional > 0:
                grouped[tenor].append((rate, notional))
                filtered += 1
        except (KeyError, TypeError, ValueError):
            continue
    curve = []
    for tenor in TENORS:
        values = grouped[tenor]
        if not values:
            continue
        total = sum(weight for _, weight in values)
        curve.append({"tenor_years": tenor, "rate": round(sum(rate * weight for rate, weight in values) / total, 8), "trade_count": len(values), "notional": round(total, 2)})
    return {"date": stamp.replace("_", "-"), "curve": curve, "filtered_trade_count": filtered}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2025-09-03")
    parser.add_argument("--end", default="2026-09-03")
    parser.add_argument("--suffix", default="")
    args = parser.parse_args()
    start = dt.date.fromisoformat(args.start)
    end = dt.date.fromisoformat(args.end)
    days = [start + dt.timedelta(days=i) for i in range((end - start).days + 1) if (start + dt.timedelta(days=i)).weekday() < 5]
    results = []
    missing = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        for day, result in zip(days, pool.map(fetch_one, days)):
            stamp, payload, status = result
            if payload is None:
                missing.append({"date": day.isoformat(), "status": status})
                continue
            results.append(parse_file(stamp, payload))
            print(f"{len(results)}/{len(days)} {day.isoformat()} filtered={results[-1]['filtered_trade_count']}", flush=True)
    results.sort(key=lambda item: item["date"])
    output_path = OUT_PATH.with_name(OUT_PATH.stem + args.suffix + OUT_PATH.suffix)
    manifest_path = MANIFEST_PATH.with_name(MANIFEST_PATH.stem + args.suffix + MANIFEST_PATH.suffix)
    atomic_json(output_path, results)
    atomic_json(manifest_path, {"start_date": start.isoformat(), "end_date": end.isoformat(), "requested_weekdays": len(days), "available_files": len(results), "missing_dates": missing, "method": "notional-weighted fixed rate by nearest maturity bucket", "source_url": URL})
    print(json.dumps({"requested_weekdays": len(days), "available_files": len(results), "missing_dates": missing, "output": str(output_path)}))


if __name__ == "__main__":
    main()
