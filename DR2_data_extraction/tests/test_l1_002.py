import json
import os
from datetime import date, timedelta

import pytest

from goldrush2.dr2.collectors import fred
from goldrush2.dr2.collectors.fred import FredNetworkError
from goldrush2.dr2.extractors import l1_002


def make_observations(count=252, value=2.0):
    start = date(2024, 1, 1)
    return [
        {"date": (start + timedelta(days=index)).isoformat(), "value": value}
        for index in range(count)
    ]


def raw_payload(observations, *, include_missing=False):
    rows = [
        {"date": observation["date"], "value": str(observation["value"])}
        for observation in observations
    ]
    if include_missing:
        rows.insert(1, {"date": "2024-01-02", "value": "."})
    return {"observations": rows}


def test_missing_marker_is_ignored_for_l1_002_source_data():
    observations = make_observations(count=3)

    parsed = fred.parse_observations(raw_payload(observations, include_missing=True))

    assert len(parsed) == 3
    assert all(row["value"] != "." for row in parsed)


def test_build_output_covers_all_signal_directions_and_inapplicable_horizon():
    observations = make_observations()
    observations[-5]["value"] = 2.1
    observations[-63]["value"] = 1.9
    observations[-252]["value"] = 2.0

    output = l1_002.build_output(observations, as_of_date="2026-09-01")

    assert output["horizons"]["1-5d"]["signal"] == 1
    assert output["horizons"]["1-3m"]["signal"] == -1
    assert output["horizons"]["1-3y"]["signal"] == 0
    assert output["horizons"]["3-10y"] == {
        "signal": 0,
        "confidence": 1,
        "evidence": {
            "data": {
                "current_value": None,
                "current_date": None,
                "comparison_value": None,
                "comparison_date": None,
                "change_percentage_points": None,
            },
            "summary": (
                "3–10 year horizon is structurally inapplicable for a 5-year "
                "maturity instrument."
            ),
        },
    }


def test_insufficient_history_returns_zero_confidence_only_for_applicable_horizons():
    output = l1_002.build_output(make_observations(count=4))

    assert output["horizons"]["1-5d"]["signal"] == 0
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert output["horizons"]["1-5d"]["evidence"]["summary"].startswith("MISSING DATA")
    assert output["horizons"]["3-10y"]["confidence"] == 1


def test_malformed_source_data_is_rejected():
    with pytest.raises(fred.FredDataError):
        fred.parse_observations(
            {"observations": [{"date": "2026-08-28", "value": "not-a-number"}]}
        )


def test_source_failure_uses_cache_younger_than_seven_days(monkeypatch, tmp_path, capsys):
    raw_path = tmp_path / "DFII5.json"
    output_path = tmp_path / "L1-002.json"
    raw_path.write_text(json.dumps(raw_payload(make_observations())), encoding="utf-8")
    monkeypatch.setattr(
        l1_002,
        "fetch_series",
        lambda *args, **kwargs: (_ for _ in ()).throw(FredNetworkError("offline")),
    )
    monkeypatch.setattr(l1_002.time, "time", lambda: 1_000_000.0)
    os.utime(raw_path, (1_000_000.0 - 6 * 86400, 1_000_000.0 - 6 * 86400))

    output = l1_002.run(raw_path=raw_path, output_path=output_path)

    assert capsys.readouterr().out.strip() == "SOURCE UNAVAILABLE — cached data used"
    assert output["horizons"]["1-5d"]["confidence"] == 1
    assert "SOURCE UNAVAILABLE — cached data used" in output["horizons"]["1-5d"]["evidence"]["summary"]
    assert output["horizons"]["3-10y"]["confidence"] == 1


@pytest.mark.parametrize("age_days", [7, 8])
def test_source_failure_rejects_cache_at_or_beyond_seven_days(monkeypatch, tmp_path, age_days):
    raw_path = tmp_path / "DFII5.json"
    output_path = tmp_path / "L1-002.json"
    raw_path.write_text(json.dumps(raw_payload(make_observations())), encoding="utf-8")
    monkeypatch.setattr(
        l1_002,
        "fetch_series",
        lambda *args, **kwargs: (_ for _ in ()).throw(FredNetworkError("offline")),
    )
    monkeypatch.setattr(l1_002.time, "time", lambda: 1_000_000.0)
    os.utime(raw_path, (1_000_000.0 - age_days * 86400, 1_000_000.0 - age_days * 86400))

    output = l1_002.run(raw_path=raw_path, output_path=output_path)

    for horizon in ("1-5d", "1-3m", "1-3y"):
        result = output["horizons"][horizon]
        assert result["signal"] == 0
        assert result["confidence"] == 0
        assert result["evidence"]["summary"].startswith("STALE DATA")
    assert output["horizons"]["3-10y"]["confidence"] == 1


def test_source_failure_without_cache_returns_zero_confidence_for_applicable_horizons(
    monkeypatch, tmp_path
):
    output_path = tmp_path / "L1-002.json"
    monkeypatch.setattr(
        l1_002,
        "fetch_series",
        lambda *args, **kwargs: (_ for _ in ()).throw(FredNetworkError("offline")),
    )

    output = l1_002.run(raw_path=tmp_path / "missing.json", output_path=output_path)

    for horizon in ("1-5d", "1-3m", "1-3y"):
        result = output["horizons"][horizon]
        assert result["signal"] == 0
        assert result["confidence"] == 0
        assert result["evidence"]["summary"].startswith("SOURCE UNAVAILABLE")
    assert output["horizons"]["3-10y"]["confidence"] == 1
