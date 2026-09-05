from datetime import date, timedelta
import json

from goldrush2.dr2.extractors import l3_001


def rows(count=261, rising=False):
    start = date(2020, 1, 1)
    return [{"date": (start + timedelta(days=i)).isoformat(), "rate": (4.0 + i / 100 if rising else 4.0 - i / 100)} for i in range(count)]


def test_signal_falling_rate_is_bullish():
    assert l3_001.build_output(rows(rising=False))["horizons"]["1-5d"]["signal"] == 1


def test_signal_rising_rate_is_bearish():
    assert l3_001.build_output(rows(rising=True))["horizons"]["1-5d"]["signal"] == -1


def test_signal_unchanged_is_neutral():
    values = [{"date": (date(2020, 1, 1) + timedelta(days=i)).isoformat(), "rate": 4.0} for i in range(261)]
    assert l3_001.build_output(values)["horizons"]["1-5d"]["signal"] == 0


def test_graded_confidence():
    horizons = l3_001.build_output(rows())["horizons"]
    assert [horizons[k]["confidence"] for k in ("1-5d", "1-3m", "1-3y", "3-10y")] == [1.0, 0.8, 0.6, 0.4]


def test_insufficient_data():
    result = l3_001.build_output(rows(5))["horizons"]["1-3m"]
    assert result["signal"] == 0 and result["confidence"] == 0.0


def test_all_horizons_present():
    assert set(l3_001.build_output(rows())["horizons"]) == set(l3_001.HORIZONS)


def test_reads_shared_l1_cache(tmp_path):
    cache = tmp_path / "L1-006.json"
    output_path = tmp_path / "L3-001.json"
    cache.write_text(json.dumps(rows()))
    result = l3_001.run(cache_path=cache, output_path=output_path)
    assert result["variable_id"] == "L3-001" and output_path.exists()


def test_source_is_cme():
    assert "CME" in l3_001.SOURCE_NAME


def test_comparison_date_is_in_evidence():
    evidence = l3_001.build_output(rows())["horizons"]["1-5d"]["evidence"]["data"]
    assert "comparison_date" in evidence


def test_current_rate_in_evidence():
    evidence = l3_001.build_output(rows())["horizons"]["1-5d"]["evidence"]["data"]
    assert "current_rate" in evidence


def test_output_schema():
    output = l3_001.build_output(rows())
    assert {"variable_id", "data_frequency", "source_name", "source_url", "observation_date", "horizons"} == set(output)


def test_long_horizon_uses_260_observations():
    evidence = l3_001.build_output(rows())["horizons"]["3-10y"]["evidence"]["data"]
    assert evidence["comparison_date"] == "2020-01-01"


def test_no_l3_004_dependency():
    assert not any("l3_004" in str(value).lower() for value in l3_001.build_output(rows()).values())


def test_empty_cache_degrades():
    assert l3_001.build_output([])["observation_date"] is None

