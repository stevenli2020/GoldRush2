import json
import os
import time

import pytest

from goldrush2.dr2.collectors.fred import FredError, parse_observations
from goldrush2.dr2.extractors import l4_001


def monthly_observations(*, rate: float = 2.0, publication_date: str = "2026-08-15", months: int = 36):
    rows = []
    for index in range(months):
        year = 2024 + index // 12
        month = index % 12 + 1
        current_date = f"{year:04d}-{month:02d}-01"
        value = 100.0 * (1 + rate / 100) ** (index / 12)
        rows.append({"date": current_date, "value": value, "publication_date": publication_date})
    return rows


@pytest.mark.parametrize(
    ("rate", "signal"),
    [(1.49, -1.0), (1.50, 0.0), (2.49, 0.0), (2.50, 0.5), (3.99, 0.5), (4.00, 1.0)],
)
def test_exact_threshold_boundaries(rate, signal):
    output = l4_001._valid({"date": "2026-12-01", "publication_date": "2026-12-15", "value": 120.0, "yoy": rate, "ma": rate}, cached=False)
    assert output["signal"] == signal
    assert output["confidence"] == 1


def test_level_rises_while_smoothed_inflation_rate_falls():
    output = l4_001._valid({"date": "2026-12-01", "publication_date": "2026-12-15", "value": 125.0, "yoy": 2.0, "ma": 2.0}, cached=False)
    summary = output["evidence"]["summary"]
    assert output["signal"] == 0.0
    assert "purchasing-power erosion only" in summary
    assert "policy" not in summary.lower()


def test_publication_date_cutoff_excludes_future_release():
    rows = monthly_observations(rate=3.0)
    rows[-1]["publication_date"] = "2026-09-15"
    output = l4_001.build_output(rows, as_of_date="2026-09-10")
    assert output["observation_date"] == "2026-11-01"
    assert output["publication_date"] == "2026-08-15"
    assert output["horizons"]["1-5d"]["confidence"] == 1


def test_missing_publication_date_is_insufficient_history():
    rows = monthly_observations()
    for row in rows:
        row.pop("publication_date")
    output = l4_001.build_output(rows, as_of_date="2026-12-31")
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert "INSUFFICIENT HISTORY" in output["horizons"]["1-5d"]["evidence"]["summary"]


def test_insufficient_history_is_zero_confidence():
    output = l4_001.build_output(monthly_observations(months=23), as_of_date="2026-12-31")
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert output["horizons"]["1-5d"]["signal"] == 0


def test_stale_publication_is_zero_confidence():
    output = l4_001.build_output(monthly_observations(publication_date="2026-01-01"), as_of_date="2026-12-31")
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert "STALE DATA" in output["horizons"]["1-5d"]["evidence"]["summary"]


def test_missing_values_are_ignored():
    parsed = parse_observations({"observations": [{"date": "2026-01-01", "value": "."}, {"date": "2026-02-01", "value": "320.5"}]})
    assert parsed == [{"date": "2026-02-01", "value": 320.5}]


def test_fred_realtime_start_is_preserved_as_publication_date():
    parsed = parse_observations({"observations": [{"date": "2026-02-01", "realtime_start": "2026-02-12", "value": "320.5"}]})
    assert parsed == [{"date": "2026-02-01", "publication_date": "2026-02-12", "value": 320.5}]


def test_fresh_cache_fallback_is_degraded_without_publication_dates(monkeypatch, tmp_path):
    raw = tmp_path / "CPIAUCSL.json"
    raw.write_text(json.dumps({"observations": [{"date": "2026-01-01", "value": "320"}]}) + "\n")
    monkeypatch.setattr(l4_001, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredError("offline")))
    output = l4_001.run(raw_path=raw, output_path=tmp_path / "out.json")
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert "INSUFFICIENT HISTORY" in output["horizons"]["1-5d"]["evidence"]["summary"]


def test_stale_cache_output(monkeypatch, tmp_path):
    raw = tmp_path / "CPIAUCSL.json"
    raw.write_text(json.dumps({"observations": [{"date": "2026-01-01", "value": "320"}]}) + "\n")
    old = time.time() - 8 * 86400
    os.utime(raw, (old, old))
    monkeypatch.setattr(l4_001, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredError("offline")))
    output = l4_001.run(raw_path=raw, output_path=tmp_path / "out.json")
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert "STALE DATA" in output["horizons"]["1-5d"]["evidence"]["summary"] or "INSUFFICIENT HISTORY" in output["horizons"]["1-5d"]["evidence"]["summary"]
