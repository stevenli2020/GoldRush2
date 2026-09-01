from datetime import date, datetime
import json
import os
import sys
import time
from types import SimpleNamespace

import pytest

from goldrush2.collectors import yahoo


class FakeFrame:
    empty = False

    def __init__(self, rows):
        self.rows = rows

    def iterrows(self):
        return iter(self.rows)


def test_download_extracts_close_skips_zero_volume_and_current_day(monkeypatch):
    rows = [
        (datetime(2026, 8, 28), {"Close": 97.1, "Volume": 10}),
        (datetime(2026, 9, 1), {"Close": 97.2, "Volume": 10}),
        (datetime(2026, 8, 27), {"Close": 97.0, "Volume": 0}),
    ]
    monkeypatch.setitem(sys.modules, "yfinance", SimpleNamespace(download=lambda *args, **kwargs: FakeFrame(rows)))
    result = yahoo._download("DX-Y.NYB")
    assert result == [{"date": "2026-08-28", "value": 97.1}]


def test_download_rejects_invalid_symbol(monkeypatch):
    monkeypatch.setitem(sys.modules, "yfinance", SimpleNamespace(download=lambda *args, **kwargs: FakeFrame([])))
    with pytest.raises(yahoo.YahooDataError, match="no .*observations"):
        yahoo._download("BAD")


def test_download_accepts_index_with_zero_volume_when_all_rows_are_zero(monkeypatch):
    rows = [(datetime(2026, 8, 28), {"Close": 99.1, "Volume": 0})]
    monkeypatch.setitem(sys.modules, "yfinance", SimpleNamespace(download=lambda *args, **kwargs: FakeFrame(rows)))
    assert yahoo._download("DX-Y.NYB") == [{"date": "2026-08-28", "value": 99.1}]


def test_success_writes_cache(monkeypatch, tmp_path):
    rows = [{"date": "2026-08-28", "value": 97.1}]
    monkeypatch.setattr(yahoo, "_download", lambda symbol: rows)
    path = tmp_path / "dxy.json"
    assert yahoo.fetch_yahoo_series("DX-Y.NYB", path) == rows
    payload = json.loads(path.read_text())
    assert payload["observations"] == rows
    assert "cached_at" in payload


def test_fresh_cache_fallback_sets_status(monkeypatch, tmp_path):
    path = tmp_path / "dxy.json"
    path.write_text(json.dumps({"cached_at": "2026-08-28", "observations": [{"date": "2026-08-28", "value": 97.1}]}))
    monkeypatch.setattr(yahoo, "_download", lambda symbol: (_ for _ in ()).throw(yahoo.YahooError("offline")))
    result = yahoo.fetch_yahoo_series("DX-Y.NYB", path)
    assert result[0]["value"] == 97.1
    assert yahoo.LAST_FETCH_USED_CACHE is True


def test_stale_cache_raises(monkeypatch, tmp_path):
    path = tmp_path / "dxy.json"
    path.write_text(json.dumps({"cached_at": "2020-01-01", "observations": []}))
    old = time.time() - 8 * 86400
    os.utime(path, (old, old))
    monkeypatch.setattr(yahoo, "_download", lambda symbol: (_ for _ in ()).throw(yahoo.YahooError("offline")))
    with pytest.raises(yahoo.YahooError, match="STALE DATA"):
        yahoo.fetch_yahoo_series("DX-Y.NYB", path)


def test_failure_without_cache_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(yahoo, "_download", lambda symbol: (_ for _ in ()).throw(yahoo.YahooError("offline")))
    with pytest.raises(yahoo.YahooError, match="offline"):
        yahoo.fetch_yahoo_series("DX-Y.NYB", tmp_path / "missing.json")
