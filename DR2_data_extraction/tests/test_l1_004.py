import json
import os
from datetime import date, timedelta

from goldrush2.dr2.collectors.frb_tips import FrbTipsNetworkError
from goldrush2.dr2.extractors import l1_004


def make_observations(count=252, value=2.0):
    start = date(2024, 1, 1)
    return [
        {"date": (start + timedelta(days=index)).isoformat(), "value": value}
        for index in range(count)
    ]


def raw_csv(observations):
    rows = ["Staff research product", "Date,TIPSY02,TIPSY05"]
    rows.extend(
        f'{observation["date"]},{observation["value"]},2.5'
        for observation in observations
    )
    return "\n".join(rows) + "\n"


def test_build_output_covers_all_signal_directions_and_exact_evidence_schema():
    observations = make_observations()
    observations[-5]["value"] = 2.1
    observations[-63]["value"] = 1.9
    observations[-252]["value"] = 2.0

    output = l1_004.build_output(observations, as_of_date="2026-09-01")

    assert output["horizons"]["1-5d"]["signal"] == 1
    assert output["horizons"]["1-3m"]["signal"] == -1
    assert output["horizons"]["1-3y"]["signal"] == 0
    assert set(output["horizons"]["1-5d"]["evidence"]["data"]) == {
        "current_value",
        "current_date",
        "comparison_value",
        "comparison_date",
        "change_percentage_points",
    }
    assert all(
        output["horizons"][horizon]["confidence"] == 1
        for horizon in ("1-5d", "1-3m", "1-3y")
    )


def test_three_to_ten_year_horizon_is_structurally_inapplicable():
    output = l1_004.build_output(make_observations())

    result = output["horizons"]["3-10y"]
    assert result["signal"] == 0
    assert result["confidence"] == 1
    assert all(value is None for value in result["evidence"]["data"].values())
    assert "structurally inapplicable" in result["evidence"]["summary"]


def test_insufficient_history_returns_zero_confidence_for_applicable_horizons():
    output = l1_004.build_output(make_observations(count=4))

    assert output["horizons"]["1-5d"]["signal"] == 0
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert output["horizons"]["1-5d"]["evidence"]["summary"].startswith(
        "MISSING DATA"
    )
    assert output["horizons"]["3-10y"]["confidence"] == 1


def test_source_failure_uses_cache_younger_than_seven_days(
    monkeypatch, tmp_path, capsys
):
    raw_path = tmp_path / "real_yield_curve.csv"
    output_path = tmp_path / "L1-004.json"
    raw_path.write_text(raw_csv(make_observations()), encoding="utf-8")
    monkeypatch.setattr(
        l1_004,
        "fetch_tips_yield",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            FrbTipsNetworkError("offline")
        ),
    )
    monkeypatch.setattr(l1_004.time, "time", lambda: 1_000_000.0)
    os.utime(raw_path, (1_000_000.0 - 6 * 86400,) * 2)

    output = l1_004.run(raw_path=raw_path, output_path=output_path)

    assert capsys.readouterr().out.strip() == "SOURCE UNAVAILABLE — cached data used"
    for horizon in ("1-5d", "1-3m", "1-3y"):
        result = output["horizons"][horizon]
        assert result["confidence"] == 1
        assert "SOURCE UNAVAILABLE — cached data used" in result["evidence"]["summary"]


def test_source_failure_rejects_cache_at_seven_days(monkeypatch, tmp_path):
    raw_path = tmp_path / "real_yield_curve.csv"
    output_path = tmp_path / "L1-004.json"
    raw_path.write_text(raw_csv(make_observations()), encoding="utf-8")
    monkeypatch.setattr(
        l1_004,
        "fetch_tips_yield",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            FrbTipsNetworkError("offline")
        ),
    )
    monkeypatch.setattr(l1_004.time, "time", lambda: 1_000_000.0)
    os.utime(raw_path, (1_000_000.0 - 7 * 86400,) * 2)

    output = l1_004.run(raw_path=raw_path, output_path=output_path)

    for horizon in ("1-5d", "1-3m", "1-3y"):
        result = output["horizons"][horizon]
        assert result["signal"] == 0
        assert result["confidence"] == 0
        assert result["evidence"]["summary"].startswith("STALE DATA")
    assert output["horizons"]["3-10y"]["confidence"] == 1


def test_source_failure_without_cache_returns_dependency_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(
        l1_004,
        "fetch_tips_yield",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            FrbTipsNetworkError("offline")
        ),
    )

    output = l1_004.run(
        raw_path=tmp_path / "missing.csv",
        output_path=tmp_path / "L1-004.json",
    )

    for horizon in ("1-5d", "1-3m", "1-3y"):
        result = output["horizons"][horizon]
        assert result["signal"] == 0
        assert result["confidence"] == 0
        assert result["evidence"]["summary"].startswith("SOURCE UNAVAILABLE")
    assert json.loads((tmp_path / "L1-004.json").read_text())["variable_id"] == "L1-004"


def test_source_failure_with_malformed_fresh_cache_returns_extraction_failure(
    monkeypatch, tmp_path
):
    raw_path = tmp_path / "real_yield_curve.csv"
    raw_path.write_text("not the expected dataset\n", encoding="utf-8")
    monkeypatch.setattr(
        l1_004,
        "fetch_tips_yield",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            FrbTipsNetworkError("offline")
        ),
    )

    output = l1_004.run(
        raw_path=raw_path,
        output_path=tmp_path / "L1-004.json",
    )

    for horizon in ("1-5d", "1-3m", "1-3y"):
        assert output["horizons"][horizon]["confidence"] == 0
        assert output["horizons"][horizon]["evidence"]["summary"].startswith(
            "EXTRACTION FAILED"
        )
