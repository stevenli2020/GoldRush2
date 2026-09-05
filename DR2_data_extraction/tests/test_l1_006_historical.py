import pandas as pd
import pytest

from goldrush2.dr2.collectors import cme


def sample_frame(periods=530):
    index = pd.date_range("2016-01-04", periods=periods, freq="W-MON")
    return pd.DataFrame({"Close": [95.0 + i / 100 for i in range(periods)]}, index=index)


def test_normalize_zq_history_produces_weekly_rates():
    rows = cme.normalize_zq_history(sample_frame())
    assert len(rows) >= 260
    assert rows[0]["date"] == "2016-01-04"
    assert rows[0]["rate"] == 5.0
    assert rows[-1]["date"] == "2026-02-23"


def test_normalize_zq_history_converts_price_to_implied_rate():
    frame = pd.DataFrame({"Close": [96.25]}, index=pd.to_datetime(["2026-09-02"]))
    assert cme.normalize_zq_history(frame) == [{"date": "2026-09-02", "rate": 3.75}]


def test_refresh_zq_history_writes_raw_and_normalized_cache(tmp_path, monkeypatch):
    import yfinance
    monkeypatch.setattr(yfinance, "download", lambda *args, **kwargs: sample_frame())
    rows = cme.refresh_zq_history(force=True, raw_path=tmp_path / "raw.json", cache_path=tmp_path / "cache.json")
    assert len(rows) >= 260
    assert (tmp_path / "raw.json").exists()
    assert (tmp_path / "cache.json").exists()


def test_refresh_zq_history_reuses_fresh_cache(tmp_path, monkeypatch):
    cache = tmp_path / "cache.json"
    cache.write_text('[{"date":"2026-09-02","rate":3.75}]', encoding="utf-8")
    import yfinance
    monkeypatch.setattr(yfinance, "download", lambda *args, **kwargs: pytest.fail("fresh cache should be reused"))
    assert cme.refresh_zq_history(cache_path=cache, raw_path=tmp_path / "raw.json") == [{"date": "2026-09-02", "rate": 3.75}]


def test_refresh_zq_history_force_refreshes(tmp_path, monkeypatch):
    import yfinance
    calls = []
    monkeypatch.setattr(yfinance, "download", lambda *args, **kwargs: calls.append(True) or sample_frame())
    cme.refresh_zq_history(force=True, raw_path=tmp_path / "raw.json", cache_path=tmp_path / "cache.json")
    assert calls == [True]
