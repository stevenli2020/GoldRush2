import json
import os
import calendar
from datetime import date

import pytest

from goldrush2.dr2.collectors.fred import FredNetworkError
from goldrush2.dr2.extractors import l1_005


def make_observations(count=36, value=0.10):
    start_year, start_month = 2023, 1
    return [
        {
            "date": date(
                start_year + (start_month - 1 + index) // 12,
                (start_month - 1 + index) % 12 + 1,
                calendar.monthrange(
                    start_year + (start_month - 1 + index) // 12,
                    (start_month - 1 + index) % 12 + 1,
                )[1],
            ).isoformat(),
            "value": value,
        }
        for index in range(count)
    ]


def raw_payload(observations):
    return {
        "observations": [
            {"date": row["date"], "value": str(row["value"])} for row in observations
        ]
    }


def test_build_output_covers_all_signal_directions_and_monthly_metadata():
    observations = make_observations()
    observations[-3]["value"] = 0.20
    observations[-12]["value"] = 0.00
    observations[-36]["value"] = 0.10

    output = l1_005.build_output(observations, as_of_date="2026-09-01")

    assert output["horizons"]["1-3m"]["signal"] == 1
    assert output["horizons"]["1-3y"]["signal"] == -1
    assert output["horizons"]["3-10y"]["signal"] == 0
    assert output["data_frequency"] == "Monthly"
    assert output["source_name"] == l1_005.SOURCE_NAME


def test_one_to_five_day_horizon_is_exactly_inapplicable():
    result = l1_005.build_output(make_observations())["horizons"]["1-5d"]

    assert result == {
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
            "summary": "1-5 day horizon is not applicable for monthly THREEFFTP10 data.",
        },
    }


def test_unchanged_term_premium_is_neutral():
    output = l1_005.build_output(make_observations())

    assert output["horizons"]["1-3m"]["signal"] == 0
    assert output["horizons"]["1-3m"]["confidence"] == 1


def test_missing_marker_is_ignored_by_fred_parser():
    observations = make_observations(4)
    observations.insert(1, {"date": "2023-02-01", "value": "."})

    from goldrush2.dr2.collectors import fred

    parsed = fred.parse_observations(raw_payload(observations))
    assert len(parsed) == 4


def test_insufficient_history_degrades_applicable_horizons():
    output = l1_005.build_output(make_observations(2))

    for horizon in ("1-3m", "1-3y", "3-10y"):
        result = output["horizons"][horizon]
        assert result["signal"] == 0
        assert result["confidence"] == 0
        assert result["evidence"]["summary"].startswith("MISSING DATA")


def test_source_failure_uses_fresh_cache_and_annotates(monkeypatch, tmp_path, capsys):
    observations = make_observations()
    raw_path = tmp_path / "ACMTP10.json"
    raw_path.write_text(json.dumps(raw_payload(observations)), encoding="utf-8")
    monkeypatch.setattr(
        l1_005,
        "fetch_series",
        lambda *args, **kwargs: (_ for _ in ()).throw(FredNetworkError("offline")),
    )
    now = 1_000_000.0
    monkeypatch.setattr(l1_005.time, "time", lambda: now)
    os.utime(raw_path, (now - 6 * 86400,) * 2)

    output = l1_005.run(raw_path=raw_path, output_path=tmp_path / "L1-005.json")

    assert capsys.readouterr().out.strip() == "SOURCE UNAVAILABLE — cached data used"
    for horizon in ("1-3m", "1-3y", "3-10y"):
        assert output["horizons"][horizon]["confidence"] == 1
        assert "SOURCE UNAVAILABLE — cached data used" in output["horizons"][horizon]["evidence"]["summary"]


def test_source_failure_rejects_cache_at_seven_days(monkeypatch, tmp_path):
    observations = make_observations()
    raw_path = tmp_path / "ACMTP10.json"
    raw_path.write_text(json.dumps(raw_payload(observations)), encoding="utf-8")
    monkeypatch.setattr(
        l1_005,
        "fetch_series",
        lambda *args, **kwargs: (_ for _ in ()).throw(FredNetworkError("offline")),
    )
    now = 1_000_000.0
    monkeypatch.setattr(l1_005.time, "time", lambda: now)
    os.utime(raw_path, (now - 7 * 86400,) * 2)

    output = l1_005.run(raw_path=raw_path, output_path=tmp_path / "L1-005.json")

    for horizon in ("1-3m", "1-3y", "3-10y"):
        result = output["horizons"][horizon]
        assert result["signal"] == 0
        assert result["confidence"] == 0
        assert result["evidence"]["summary"].startswith("STALE DATA")


def test_source_failure_without_cache_returns_source_unavailable(monkeypatch, tmp_path):
    monkeypatch.setattr(
        l1_005,
        "fetch_series",
        lambda *args, **kwargs: (_ for _ in ()).throw(FredNetworkError("offline")),
    )

    output = l1_005.run(
        raw_path=tmp_path / "missing.json", output_path=tmp_path / "L1-005.json"
    )

    for horizon in ("1-3m", "1-3y", "3-10y"):
        assert output["horizons"][horizon]["evidence"]["summary"].startswith(
            "SOURCE UNAVAILABLE"
        )
