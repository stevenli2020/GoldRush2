import json
from pathlib import Path

from goldrush2.collectors.fedwatch import FedWatchCollector


def payload():
    return {"current_target": "3.50%-3.75%", "meeting_date": "2026-09-16", "contract": "ZQU6", "history": [{"trade_date": "2026-08-28", "probabilities": {"3.50%-3.75%": 66.0, "3.75%-4.00%": 34.0}}, {"trade_date": "2026-09-01", "probabilities": {"3.50%-3.75%": 38.0, "3.75%-4.00%": 62.0}}]}


def test_collector_normalizes_cut_probability():
    rows = FedWatchCollector._normalize(payload())
    assert rows[-1]["cut_probability"] == 0.0
    assert rows[-1]["meeting_date"] == "2026-09-16"


def test_collector_sums_lower_target_bands():
    data = {"current_target": "4.00%-4.25%"}
    assert FedWatchCollector._cut_probability({"3.75%-4.00%": 30, "4.00%-4.25%": 50, "4.25%-4.50%": 20}, data["current_target"]) == 30


def test_collector_ignores_malformed_bands():
    assert FedWatchCollector._cut_probability({"bad": 100}, "4.00%-4.25%") == 0


def test_collector_cache_path(tmp_path):
    c = FedWatchCollector(tmp_path / "cache", tmp_path / "raw")
    assert c.cache_path == tmp_path / "cache" / "l3_004.json"


def test_collector_writes_raw_and_cache(monkeypatch, tmp_path):
    c = FedWatchCollector(tmp_path / "cache", tmp_path / "raw")
    monkeypatch.setattr(c, "_fetch", payload)
    assert c.fetch().exists()
    assert c.raw_path.exists()
    assert json.loads(c.cache_path.read_text())[0]["date"] == "2026-08-28"


def test_collector_uses_existing_cache(monkeypatch, tmp_path):
    c = FedWatchCollector(tmp_path / "cache", tmp_path / "raw")
    c.cache_path.parent.mkdir(parents=True)
    c.cache_path.write_text("[]")
    monkeypatch.setattr(c, "_fetch", lambda: (_ for _ in ()).throw(AssertionError("cache expected")))
    assert c.fetch().exists()


def test_collector_force_refresh(monkeypatch, tmp_path):
    c = FedWatchCollector(tmp_path / "cache", tmp_path / "raw")
    monkeypatch.setattr(c, "_fetch", payload)
    c.fetch()
    monkeypatch.setattr(c, "_fetch", lambda: {**payload(), "history": payload()["history"] + [{"trade_date": "2026-09-02", "probabilities": {"3.50%-3.75%": 20, "3.75%-4.00%": 80}}]})
    c.fetch(force=True)
    assert len(json.loads(c.cache_path.read_text())) == 3


def test_collector_missing_history_raises(monkeypatch, tmp_path):
    c = FedWatchCollector(tmp_path / "cache", tmp_path / "raw")
    monkeypatch.setattr(c, "_fetch", lambda: {"history": []})
    import pytest
    with pytest.raises(RuntimeError, match="no probability history"):
        c.fetch()


def test_collector_source_metadata_is_preserved(tmp_path):
    c = FedWatchCollector(tmp_path / "cache", tmp_path / "raw")
    assert c.SOURCE_NAME.startswith("CME FedWatch")


def test_collector_verbose_request_lifecycle(monkeypatch, tmp_path, capsys):
    c = FedWatchCollector(tmp_path / "cache", tmp_path / "raw", verbose=2)
    import cme_fedwatch
    monkeypatch.setattr(cme_fedwatch, "get_history", lambda **kwargs: payload())
    c._fetch()
    output = capsys.readouterr().out
    assert "CME FedWatch request started" in output
    assert "CME FedWatch request completed" in output


def test_collector_normalizes_sorted_unique_dates():
    data = payload()
    data["history"] = [data["history"][1], data["history"][0], data["history"][1]]
    rows = FedWatchCollector._normalize(data)
    assert [row["date"] for row in rows] == ["2026-08-28", "2026-09-01"]
