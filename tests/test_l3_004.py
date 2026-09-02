from datetime import date, timedelta
import json

from goldrush2.extractors import l3_004


def rows(count=261, rising=False, meeting_date="2026-09-16"):
    start = date(2026, 1, 1)
    return [{"date": (start + timedelta(days=i)).isoformat(), "cut_probability": (i if rising else 100 - i), "meeting_date": meeting_date} for i in range(count)]


def test_signal_rising_probability_is_bullish():
    assert l3_004.build_output(rows(rising=True))["horizons"]["1-5d"]["signal"] == 1


def test_signal_falling_probability_is_bearish():
    assert l3_004.build_output(rows(rising=False))["horizons"]["1-5d"]["signal"] == -1


def test_signal_unchanged_is_neutral():
    values = [{"date": (date(2026, 1, 1) + timedelta(days=i)).isoformat(), "cut_probability": 10, "meeting_date": "2026-09-16"} for i in range(261)]
    assert l3_004.build_output(values)["horizons"]["1-5d"]["signal"] == 0


def test_confidence_near_meeting():
    result = l3_004.build_output(rows())["horizons"]["1-5d"]
    assert result["confidence"] == 0.9


def test_confidence_mid_range():
    values = rows(meeting_date="2026-10-01")
    assert l3_004.build_output(values)["horizons"]["1-5d"]["confidence"] == 0.7


def test_confidence_far_meeting():
    values = rows(meeting_date="2027-01-01")
    assert l3_004.build_output(values)["horizons"]["1-5d"]["confidence"] == 0.5


def test_confidence_no_meeting():
    values = rows(meeting_date=None)
    assert l3_004.build_output(values)["horizons"]["1-5d"]["confidence"] == 0.3


def test_insufficient_data():
    result = l3_004.build_output(rows(5))["horizons"]["1-3m"]
    assert result["signal"] == 0 and result["confidence"] == 0.0


def test_all_horizons_present():
    assert set(l3_004.build_output(rows())["horizons"]) == set(l3_004.HORIZONS)


def test_forward_filled_series_can_be_consumed():
    values = rows(14)
    values[5]["cut_probability"] = values[4]["cut_probability"]
    assert "signal" in l3_004.build_output(values)["horizons"]["1-5d"]


def test_meeting_date_in_evidence():
    assert l3_004.build_output(rows())["horizons"]["1-5d"]["evidence"]["data"]["meeting_date"] == "2026-09-16"


def test_no_l10_dependency():
    assert not any("l10" in str(value).lower() for value in l3_004.build_output(rows()).values())


def test_output_schema():
    output = l3_004.build_output(rows())
    assert {"variable_id", "data_frequency", "source_name", "source_url", "observation_date", "horizons"} == set(output)


def test_atomic_run(tmp_path):
    cache = tmp_path / "l3_004.json"
    output_path = tmp_path / "L3-004.json"
    cache.write_text(json.dumps(rows()))
    assert l3_004.run(cache_path=cache, output_path=output_path)["variable_id"] == "L3-004"
