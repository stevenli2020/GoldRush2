import json

from goldrush2.collectors.fedwatch import FedWatchCollector


def write_csv(path, rows):
    path.write_text("Date,(325-350),(350-375),(375-400)\n" + "\n".join(f"{d},{a},{b},{c}" for d, a, b, c in rows) + "\n", encoding="utf-8")


def test_collector_parses_csv_and_easing_probability(tmp_path):
    path = tmp_path / "FedMeeting_20260916.csv"
    write_csv(path, [("09/01/2026", "0.25", "0.50", "0.25")])
    rows = FedWatchCollector.parse_csv(path)
    assert rows[0]["date"] == "2026-09-01"
    assert rows[0]["easing_prob"] == 25.0
    assert rows[0]["is_filled"] is False


def test_collector_excludes_hike_bands(tmp_path):
    path = tmp_path / "FedMeeting_20260916.csv"
    write_csv(path, [("09/01/2026", "0.25", "0.50", "0.25")])
    assert FedWatchCollector.parse_csv(path)[0]["easing_prob"] == 25.0


def test_collector_accepts_signed_probability_columns(tmp_path):
    path = tmp_path / "signed.csv"
    path.write_text("Date,-25,0,+25\n2026-09-01,0.30,0.50,0.20\n", encoding="utf-8")
    assert FedWatchCollector.parse_csv(path)[0]["easing_prob"] == 30.0


def test_collector_forward_fills_and_marks_missing_days(tmp_path):
    path = tmp_path / "FedMeeting_20260916.csv"
    write_csv(path, [("09/04/2026", "0.20", "0.60", "0.20"), ("09/08/2026", "0.30", "0.50", "0.20")])
    rows = FedWatchCollector.parse_csv(path)
    filled = next(row for row in rows if row["date"] == "2026-09-05")
    assert filled["is_filled"] is True
    assert filled["easing_prob"] == 20.0
    assert filled["filled_from"] == "2026-09-04"


def test_collector_appends_meeting_date(tmp_path):
    path = tmp_path / "FedMeeting_20260916.csv"
    write_csv(path, [("09/01/2026", "0.25", "0.50", "0.25")])
    rows = FedWatchCollector.parse_csv(path, meeting_date=__import__("datetime").date(2026, 9, 16))
    assert rows[-1]["date"] == "2026-09-16"
    assert rows[-1]["is_filled"] is True


def test_collector_missing_csv_raises(tmp_path):
    c = FedWatchCollector(tmp_path / "cache", tmp_path / "raw")
    c.csv_path = tmp_path / "missing.csv"
    import pytest
    with pytest.raises(RuntimeError, match="Cannot determine meeting date"):
        c.fetch(force=True)


def test_collector_writes_cache_and_raw(tmp_path):
    source = tmp_path / "FedMeeting_20260916.csv"
    write_csv(source, [("09/01/2026", "0.25", "0.50", "0.25")])
    c = FedWatchCollector(tmp_path / "cache", tmp_path / "raw")
    c.csv_path = source
    result = c.fetch(force=True)
    assert result.exists()
    assert json.loads(result.read_text())[0]["easing_prob"] == 25.0
    assert c.raw_path.exists()
    metadata = json.loads(c.meta_path.read_text())
    assert metadata["last_observation_date"] == "2026-09-16"


def test_collector_uses_fresh_cache(tmp_path, monkeypatch):
    c = FedWatchCollector(tmp_path / "cache", tmp_path / "raw")
    c.cache_path.parent.mkdir(parents=True)
    c.cache_path.write_text('[{"date":"2026-09-01","easing_prob":25,"is_filled":false}]')
    monkeypatch.setattr(c, "_meeting_date", lambda: __import__("datetime").date(2026, 9, 16))
    monkeypatch.setattr(c, "parse_csv", lambda *args: (_ for _ in ()).throw(AssertionError("cache expected")))
    assert c.fetch().exists()


def test_collector_force_refreshes(tmp_path):
    source = tmp_path / "FedMeeting_20260916.csv"
    write_csv(source, [("09/01/2026", "0.25", "0.50", "0.25")])
    c = FedWatchCollector(tmp_path / "cache", tmp_path / "raw")
    c.csv_path = source
    c.fetch(force=True)
    write_csv(source, [("09/01/2026", "0.40", "0.40", "0.20")])
    c.fetch(force=True)
    assert json.loads(c.cache_path.read_text())[0]["easing_prob"] == 40.0
