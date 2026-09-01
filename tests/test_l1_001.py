import json
import os
from datetime import date, timedelta

import pytest

from goldrush2.collectors.fred import FredNetworkError
from goldrush2.extractors import l1_001


def make_observations(count=756, value=2.0):
    start = date(2024, 1, 1)
    return [
        {"date": (start + timedelta(days=index)).isoformat(), "value": value}
        for index in range(count)
    ]


def raw_payload(observations):
    return {
        "observations": [
            {"date": observation["date"], "value": str(observation["value"])}
            for observation in observations
        ]
    }


def test_build_output_covers_all_signal_directions_and_strict_evidence_schema():
    observations = make_observations()
    observations[-5]["value"] = 2.1
    observations[-63]["value"] = 1.9
    observations[-252]["value"] = 2.0
    observations[-756]["value"] = 2.2

    output = l1_001.build_output(observations, as_of_date="2026-09-01")

    assert output["horizons"]["1-5d"]["signal"] == 1
    assert output["horizons"]["1-3m"]["signal"] == -1
    assert output["horizons"]["1-3y"]["signal"] == 0
    assert output["horizons"]["3-10y"]["signal"] == 1
    assert set(output["horizons"]) == set(l1_001.HORIZON_LOOKBACKS)
    assert output["observation_date"] == observations[-1]["date"]

    for result in output["horizons"].values():
        assert result["confidence"] == 1
        assert set(result) == {"signal", "confidence", "evidence"}
        assert set(result["evidence"]) == {"data", "summary"}
        assert set(result["evidence"]["data"]) == {
            "current_value",
            "current_date",
            "comparison_value",
            "comparison_date",
            "change_percentage_points",
        }


def test_five_observations_are_sufficient_for_five_observation_lookback():
    observations = make_observations(count=5)

    output = l1_001.build_output(observations)

    assert output["horizons"]["1-5d"]["confidence"] == 1
    assert output["horizons"]["1-3m"]["confidence"] == 0


def test_insufficient_history_returns_zero_confidence_with_reason():
    output = l1_001.build_output(make_observations(count=4))

    result = output["horizons"]["1-5d"]
    assert result["signal"] == 0
    assert result["confidence"] == 0
    assert result["evidence"]["summary"].startswith("MISSING DATA")
    assert "5 valid observations are required; 4 are available" in result["evidence"]["summary"]


def test_source_failure_uses_cache_younger_than_seven_days(monkeypatch, tmp_path, capsys):
    raw_path = tmp_path / "DFII10.json"
    output_path = tmp_path / "L1-001.json"
    raw_path.write_text(json.dumps(raw_payload(make_observations())), encoding="utf-8")
    monkeypatch.setattr(l1_001, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredNetworkError("offline")))
    monkeypatch.setattr(l1_001.time, "time", lambda: 1_000_000.0)
    os.utime(raw_path, (1_000_000.0 - 6 * 86400, 1_000_000.0 - 6 * 86400))

    output = l1_001.run(raw_path=raw_path, output_path=output_path)

    assert capsys.readouterr().out.strip() == "SOURCE UNAVAILABLE — cached data used"
    assert output["horizons"]["1-5d"]["confidence"] == 1
    assert "SOURCE UNAVAILABLE — cached data used" in output["horizons"]["1-5d"]["evidence"]["summary"]
    assert json.loads(output_path.read_text(encoding="utf-8")) == output


@pytest.mark.parametrize("age_days", [7, 8])
def test_source_failure_rejects_cache_at_or_beyond_seven_days(monkeypatch, tmp_path, age_days):
    raw_path = tmp_path / "DFII10.json"
    output_path = tmp_path / "L1-001.json"
    raw_path.write_text(json.dumps(raw_payload(make_observations())), encoding="utf-8")
    monkeypatch.setattr(l1_001, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredNetworkError("offline")))
    monkeypatch.setattr(l1_001.time, "time", lambda: 1_000_000.0)
    os.utime(raw_path, (1_000_000.0 - age_days * 86400, 1_000_000.0 - age_days * 86400))

    output = l1_001.run(raw_path=raw_path, output_path=output_path)

    for result in output["horizons"].values():
        assert result["signal"] == 0
        assert result["confidence"] == 0
        assert result["evidence"]["summary"].startswith("STALE DATA")


def test_source_failure_without_cache_returns_zero_confidence(monkeypatch, tmp_path):
    output_path = tmp_path / "L1-001.json"
    monkeypatch.setattr(l1_001, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredNetworkError("offline")))

    output = l1_001.run(raw_path=tmp_path / "missing.json", output_path=output_path)

    for result in output["horizons"].values():
        assert result["signal"] == 0
        assert result["confidence"] == 0
        assert result["evidence"]["summary"].startswith("SOURCE UNAVAILABLE")


def test_successful_source_overwrites_cache(monkeypatch, tmp_path):
    raw_path = tmp_path / "DFII10.json"
    output_path = tmp_path / "L1-001.json"
    raw_path.write_text('{"old": true}', encoding="utf-8")
    observations = make_observations()

    def successful_fetch(series_id, *, raw_path):
        raw_path.write_text(json.dumps(raw_payload(observations)), encoding="utf-8")
        return observations

    monkeypatch.setattr(l1_001, "fetch_series", successful_fetch)

    output = l1_001.run(raw_path=raw_path, output_path=output_path)

    assert output["horizons"]["3-10y"]["confidence"] == 1
    assert json.loads(raw_path.read_text(encoding="utf-8"))["observations"]
