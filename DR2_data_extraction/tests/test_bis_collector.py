import json
from pathlib import Path

import pytest

from goldrush2.dr2.collectors.bis import BISCollector, parse_csv, quarter_end


HEADER = "FREQ,BORROWERS_CTY,TC_BORROWERS,TC_LENDERS,VALUATION,UNIT_TYPE,UNIT_MULT,TC_ADJUST,TIME_PERIOD,OBS_VALUE\n"


def csv_bytes(rows):
    return (HEADER + "\n".join(f"Q,5A,P,A,M,USD,9,A,{period},{value}" for period, value in rows) + "\n").encode()


def test_quarter_end_conversion():
    assert quarter_end("2025-Q1") == "2025-03-31"
    assert quarter_end("2025-Q2") == "2025-06-30"
    assert quarter_end("2025-Q3") == "2025-09-30"
    assert quarter_end("2025-Q4") == "2025-12-31"


def test_invalid_period_rejected():
    with pytest.raises(ValueError):
        quarter_end("2025-Q5")


def test_csv_filters_dimensions_and_parses():
    data = csv_bytes([("2024-Q1", 100), ("2024-Q2", 105)]) + b"Q,5A,P,B,M,USD,9,A,2024-Q3,110\n"
    assert parse_csv(data) == [{"date": "2024-03-31", "value": 100.0}, {"date": "2024-06-30", "value": 105.0}]


@pytest.mark.parametrize("value", ["", ".", "abc", "0", "-2", "nan", "inf"])
def test_invalid_values(value):
    with pytest.raises(ValueError):
        parse_csv(csv_bytes([("2024-Q1", value)]))


def test_duplicate_conflict_rejected():
    with pytest.raises(ValueError, match="conflicting duplicate"):
        parse_csv(csv_bytes([("2024-Q1", 100), ("2024-Q1", 101)]))


def test_collector_full_download_writes_raw(monkeypatch, tmp_path):
    collector = BISCollector(tmp_path / "cache", tmp_path / "raw" / "series.csv")
    monkeypatch.setattr(collector, "_fetch", lambda: csv_bytes([("2024-Q1", 100)]))
    assert collector.download_full() == [{"date": "2024-03-31", "value": 100.0}]
    assert collector.raw_path.exists()


def test_collector_incremental_not_supported(tmp_path):
    collector = BISCollector(tmp_path / "cache", tmp_path / "raw.csv")
    with pytest.raises(NotImplementedError):
        collector.download_incremental("2024-03-31")


def test_collector_latest_date(monkeypatch, tmp_path):
    collector = BISCollector(tmp_path / "cache", tmp_path / "raw.csv")
    monkeypatch.setattr(collector, "_fetch", lambda: csv_bytes([("2024-Q1", 100), ("2025-Q4", 120)]))
    assert collector.fetch_latest_observation_date() == "2025-12-31"

