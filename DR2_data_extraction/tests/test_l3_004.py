from datetime import date, timedelta
import json

from goldrush2.dr2.collectors.fedwatch import FedWatchCollector
from goldrush2.dr2.extractors.l3_004 import build_output, run


def rows(n=1821, rising=True, filled=False):
    start = date(2021, 9, 1)
    return [{"date": (start + timedelta(days=i)).isoformat(), "easing_prob": float(i if rising else n - i), "is_filled": filled} for i in range(n)]


def test_extractor_signal_rising():
    assert build_output(rows())["horizons"]["1-5d"]["signal"] == 1


def test_extractor_signal_falling():
    assert build_output(rows(rising=False))["horizons"]["1-5d"]["signal"] == -1


def test_extractor_signal_unchanged():
    data = rows(6)
    for item in data:
        item["easing_prob"] = 10.0
    result = build_output(data)["horizons"]["1-5d"]
    assert result["signal"] == 0
    assert result["confidence"] == 1.0


def test_extractor_graded_confidence():
    horizons = build_output(rows())["horizons"]
    assert [horizons[key]["confidence"] for key in ("1-5d", "1-3m", "1-3y", "3-10y")] == [1.0, 0.8, 0.6, 0.4]


def test_extractor_insufficient_data():
    result = build_output(rows(100))["horizons"]["3-10y"]
    assert result["signal"] == 0
    assert result["confidence"] == 0.0


def test_extractor_includes_filled_flag():
    data = rows(6, filled=True)
    evidence = build_output(data)["horizons"]["1-5d"]["evidence"]
    assert evidence["lookback_is_filled"] is True


def test_extractor_output_schema():
    output = build_output(rows())
    assert output["variable_id"] == "L3-004"
    assert output["data_frequency"] == "Daily"
    assert set(output["horizons"]) == {"1-5d", "1-3m", "1-3y", "3-10y"}


def test_extractor_uses_calendar_date_lookback():
    data = rows(100)
    evidence = build_output(data)["horizons"]["1-3m"]["evidence"]
    assert evidence["lookback_date"] == (date(2021, 9, 1) + timedelta(days=8)).isoformat()


def test_extractor_writes_output_atomically(tmp_path):
    cache = tmp_path / "cache.json"
    output_path = tmp_path / "current.json"
    cache.write_text(json.dumps(rows(6)), encoding="utf-8")
    result = run(output_path=output_path, cache_path=cache)
    assert result["variable_id"] == "L3-004"
    assert output_path.exists()


def test_extractor_signal_values_are_bounded():
    for horizon in build_output(rows())["horizons"].values():
        assert horizon["signal"] in {-1, 0, 1}


def test_collector_safe_merge_preserves_existing_dates():
    existing = [{"date": "2026-09-01", "easing_prob": 10.0, "is_filled": False}]
    incoming = [
        {"date": "2026-09-01", "easing_prob": 99.0, "is_filled": False},
        {"date": "2026-09-02", "easing_prob": 20.0, "is_filled": False},
    ]
    assert FedWatchCollector._safe_merge(existing, incoming) == [existing[0], incoming[1]]


def test_collector_safe_merge_force_replaces_cache():
    existing = [{"date": "2026-09-01", "easing_prob": 10.0, "is_filled": False}]
    incoming = [{"date": "2026-09-01", "easing_prob": 99.0, "is_filled": False}]
    assert FedWatchCollector._safe_merge(existing, incoming, force=True) == incoming


def test_extractor_evidence_contains_required_lookback_fields():
    evidence = build_output(rows())["horizons"]["1-5d"]["evidence"]
    assert {"current_easing_prob", "lookback_easing_prob", "lookback_date", "change", "lookback_is_filled"} <= set(evidence)


def test_extractor_meeting_date_is_carried_from_cache():
    data = rows(6)
    for item in data:
        item["meeting_date"] = "2026-09-16"
    assert build_output(data)["meeting_date"] == "2026-09-16"


def test_extractor_empty_cache_returns_zero_confidence():
    output = build_output([])
    assert all(item["signal"] == 0 and item["confidence"] == 0.0 for item in output["horizons"].values())


def test_extractor_uses_previous_observation_on_calendar_target():
    data = [
        {"date": "2026-09-01", "easing_prob": 10.0, "is_filled": False},
        {"date": "2026-09-02", "easing_prob": 20.0, "is_filled": False},
        {"date": "2026-09-06", "easing_prob": 30.0, "is_filled": True},
    ]
    evidence = build_output(data)["horizons"]["1-5d"]["evidence"]
    assert evidence["lookback_date"] == "2026-09-01"
