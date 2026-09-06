"""Mocked source-adapter integration tests."""

import json
from pathlib import Path
from datetime import date
from openpyxl import Workbook

from goldrush2.dr2.collectors.fred import FredCollector
from goldrush2.dr2.collectors.treasury import TreasuryCollector, fetch_latest_treasury_date
from goldrush2.dr2.collectors.wgc import WGCWorkbookCollector
from goldrush2.dr2.collectors.yahoo import YahooCollector
from goldrush2.dr2.extractors.l5_001 import parse_purchases_workbook
from goldrush2.dr2.extractors.l8_001 import parse_flows_workbook


def test_fred_full_then_incremental_refresh(monkeypatch, tmp_path):
    calls = []

    def fetch(series_id, **kwargs):
        calls.append(kwargs)
        return [{"date": "2024-01-01", "value": 1.0}] if kwargs.get("observation_start") is None else [{"date": "2024-01-02", "value": 2.0}]

    monkeypatch.setattr("goldrush2.dr2.collectors.fred.fetch_series", fetch)
    monkeypatch.setattr("goldrush2.dr2.collectors.fred.fetch_latest_series_date", lambda *args, **kwargs: "2024-01-02")
    raw_path = tmp_path / "raw.json"
    first = FredCollector(tmp_path / "cache", "TEST", raw_path)
    assert first.run() == [{"date": "2024-01-01", "value": 1.0}]
    second = FredCollector(tmp_path / "cache", "TEST", raw_path)
    assert second.run()[-1] == {"date": "2024-01-02", "value": 2.0}
    assert second.action == "incremental"
    assert any(call.get("observation_start") == "2024-01-01" for call in calls)


def test_yahoo_full_then_incremental_refresh(monkeypatch, tmp_path):
    monkeypatch.setattr("goldrush2.dr2.collectors.yahoo.fetch_yahoo_series", lambda symbol, path: [{"date": "2024-01-01", "value": 1.0}])
    monkeypatch.setattr("goldrush2.dr2.collectors.yahoo._download", lambda symbol, **kwargs: [{"date": "2024-01-02", "value": 2.0}])
    first = YahooCollector(tmp_path / "cache", "TEST", tmp_path / "raw.json")
    first.run()
    second = YahooCollector(tmp_path / "cache", "TEST", tmp_path / "raw.json")
    assert second.run()[-1] == {"date": "2024-01-02", "value": 2.0}
    assert second.action == "incremental"


def test_wgc_normalizes_workbook_and_uses_internal_observation_date(tmp_path):
    workbook = tmp_path / "source.xlsx"
    workbook.write_bytes(b"PK\x03\x04")
    collector = WGCWorkbookCollector(tmp_path / "cache", tmp_path / "raw", lambda directory, force=False: workbook, lambda path: [{"date": "2024-06-30", "value": 7.0}])
    assert collector.run() == [{"date": "2024-06-30", "value": 7.0}]
    assert collector.load_meta()["last_observation_date"] == "2024-06-30"


def test_shared_wgc_workbook_keeps_flows_and_net_changes_independent(tmp_path):
    workbook = Workbook()
    flows = workbook.active
    flows.title = "Demand by month"
    flows.append(["Date", "Value (USD)", "Fund A", "Fund B"])
    flows.append([date(2026, 7, 31), 999, 10, -2])
    monthly = workbook.create_sheet("Monthly")
    monthly.append([None, "Country", None, date(2026, 7, 31)])
    monthly.append([None, "Country A", None, 3])
    path = tmp_path / "shared.xlsx"
    workbook.save(path)
    assert parse_flows_workbook(path) == [{"date": "2026-07-31", "value": 8.0}]
    assert parse_purchases_workbook(path) == [{"date": "2026-07-31", "value": 3.0}]


def test_treasury_pagination_normalizer_and_latest_date(monkeypatch, tmp_path):
    payload = {"pages": [{"data": [{"record_date": "2024-01-31", "value": "1"}]}, {"data": [{"record_date": "2024-02-29", "value": "2"}]}]}
    monkeypatch.setattr("goldrush2.dr2.collectors.treasury.fetch_treasury_table", lambda *args: payload)
    monkeypatch.setattr("goldrush2.dr2.collectors.treasury.fetch_latest_treasury_date", lambda *args: "2024-02-29")
    collector = TreasuryCollector(tmp_path / "cache", "https://example.test", {}, tmp_path / "raw.json", lambda rows: [{"date": row["record_date"], "value": float(row["value"])} for row in rows])
    assert collector.run()[-1] == {"date": "2024-02-29", "value": 2.0}
    second = TreasuryCollector(tmp_path / "cache", "https://example.test", {}, tmp_path / "raw.json", lambda rows: [{"date": row["record_date"], "value": float(row["value"])} for row in rows])
    assert second.run()[-1]["date"] == "2024-02-29"
    assert second.action == "skip"


def test_treasury_latest_date_reads_newest_page_record(monkeypatch):
    class Response:
        def read(self):
            return json.dumps({"data": [{"record_date": "2024-03-31"}]}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr("goldrush2.dr2.collectors.treasury.urlopen", lambda *args, **kwargs: Response())
    assert fetch_latest_treasury_date("https://example.test", {}) == "2024-03-31"
