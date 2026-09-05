import os
from datetime import date, timedelta

import pytest

from goldrush2.dr2.collectors.frb_tips import FrbTipsNetworkError
from goldrush2.dr2.extractors import l1_003


def make_observations(count=756, value=2.0):
    start = date(2024, 1, 1)
    return [
        {"date": (start + timedelta(days=index)).isoformat(), "value": value}
        for index in range(count)
    ]


def raw_csv(observations2, observations5, observations10):
    rows = ["Staff research product", "Date,TIPSY02,TIPSY05,TIPSY10"]
    values5 = {row["date"]: row["value"] for row in observations5}
    values10 = {row["date"]: row["value"] for row in observations10}
    rows.extend(
        f'{row["date"]},{row["value"]},{values5[row["date"]]},{values10[row["date"]]}'
        for row in observations2
        if row["date"] in values5 and row["date"] in values10
    )
    return "\n".join(rows) + "\n"


def test_forward_formulas_match_known_values():
    assert l1_003._forward_2y3y(3.0, 2.0) == pytest.approx(
        ((((1 + 3 / 100) ** 5 / (1 + 2 / 100) ** 2) ** (1 / 3)) - 1) * 100
    )
    assert l1_003._forward_5y5y(4.0, 3.0) == pytest.approx(
        ((((1 + 4 / 100) ** 10 / (1 + 3 / 100) ** 5) ** (1 / 5)) - 1) * 100
    )


def test_composite_averages_the_two_feasible_nodes():
    value, nodes = l1_003._composite(2.0, 3.0, 4.0)

    assert value == pytest.approx((nodes["forward_2y3y"] + nodes["forward_5y5y"]) / 2)
    assert set(nodes) == {"forward_2y3y", "forward_5y5y"}


def test_missing_spot_rate_skips_the_entire_date():
    observations2 = make_observations(3)
    observations5 = make_observations(3)
    observations10 = make_observations(3)
    observations5.pop(1)

    series, _ = l1_003.build_composite_series(observations2, observations5, observations10)

    assert [row["date"] for row in series] == [observations2[0]["date"], observations2[2]["date"]]


def test_build_output_applies_all_four_signal_directions():
    observations2 = make_observations()
    observations5 = make_observations()
    observations10 = make_observations()
    observations10[-5]["value"] = 2.1
    observations10[-63]["value"] = 1.9
    observations10[-252]["value"] = 2.0
    observations10[-756]["value"] = 2.1

    output = l1_003.build_output(observations2, observations5, observations10, as_of_date="2026-09-01")

    assert output["horizons"]["1-5d"]["signal"] == 1
    assert output["horizons"]["1-3m"]["signal"] == -1
    assert output["horizons"]["1-3y"]["signal"] == 0
    assert output["horizons"]["3-10y"]["signal"] == 1
    assert set(output["forward_nodes"]) == {"forward_2y3y", "forward_5y5y"}
    assert "2Y3Y and 5Y5Y" in output["calculation_method"]
    assert "1Y1Y omitted" in output["calculation_method"]


def test_insufficient_composite_history_degrades_each_horizon():
    observations = make_observations(4)

    output = l1_003.build_output(observations, observations, observations)

    for result in output["horizons"].values():
        assert result["signal"] == 0
        assert result["confidence"] == 0
        assert result["evidence"]["summary"].startswith("MISSING DATA")


def test_cached_dependency_is_used_and_annotated(monkeypatch, tmp_path, capsys):
    observations = make_observations()
    raw_path = tmp_path / "real_yield_curve.csv"
    raw_path.write_text(raw_csv(observations, observations, observations), encoding="utf-8")
    monkeypatch.setattr(
        l1_003,
        "fetch_tips_yield",
        lambda *args, **kwargs: (_ for _ in ()).throw(FrbTipsNetworkError("offline")),
    )
    now = 1_000_000.0
    monkeypatch.setattr(l1_003.time, "time", lambda: now)
    os.utime(raw_path, (now - 6 * 86400,) * 2)

    output = l1_003.run(raw_path=raw_path, output_path=tmp_path / "L1-003.json")

    assert capsys.readouterr().out.strip() == "DEPENDENT SOURCE UNAVAILABLE — cached data used"
    for result in output["horizons"].values():
        assert result["confidence"] == 1
        assert "DEPENDENT SOURCE UNAVAILABLE — cached data used" in result["evidence"]["summary"]


def test_stale_dependency_degrades_all_horizons(monkeypatch, tmp_path):
    observations = make_observations()
    raw_path = tmp_path / "real_yield_curve.csv"
    raw_path.write_text(raw_csv(observations, observations, observations), encoding="utf-8")
    monkeypatch.setattr(
        l1_003,
        "fetch_tips_yield",
        lambda *args, **kwargs: (_ for _ in ()).throw(FrbTipsNetworkError("offline")),
    )
    now = 1_000_000.0
    monkeypatch.setattr(l1_003.time, "time", lambda: now)
    os.utime(raw_path, (now - 7 * 86400,) * 2)

    output = l1_003.run(raw_path=raw_path, output_path=tmp_path / "L1-003.json")

    for result in output["horizons"].values():
        assert result["signal"] == 0
        assert result["confidence"] == 0
        assert result["evidence"]["summary"].startswith("STALE DEPENDENT DATA")
