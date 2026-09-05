import json
import os
import time

import pytest

from goldrush2.dr2.collectors.treasury import TreasuryError
from goldrush2.dr2.extractors import l4_008


def annual_observations(count=6, comparison_index=None, current=12.0, comparison=10.0):
    rows = [{"date": f"{2020 + i}-09-30", "value": 10.0} for i in range(count)]
    if comparison_index is not None:
        rows[comparison_index]["value"] = comparison
    rows[-1]["value"] = current
    return rows


@pytest.mark.parametrize("horizon, lookback", [("1-3y", 1), ("3-10y", 5)])
@pytest.mark.parametrize("current, comparison, signal", [(12.0, 10.0, 1), (8.0, 10.0, -1), (10.0, 10.0, 0)])
def test_annual_signal_directions(horizon, lookback, current, comparison, signal):
    result = l4_008.build_output(annual_observations(comparison_index=6 - 1 - lookback, current=current, comparison=comparison))
    assert result["horizons"][horizon]["signal"] == signal
    assert result["horizons"][horizon]["confidence"] == 1


def test_parse_pairs_september_lines():
    rows = [{"record_date": "2025-09-30", "line_code_nbr": "130", "current_fytd_rcpt_outly_amt": "1,000"}, {"record_date": "2025-09-30", "line_code_nbr": "360", "current_fytd_rcpt_outly_amt": "100"}, {"record_date": "2025-06-30", "line_code_nbr": "130", "current_fytd_rcpt_outly_amt": "900"}]
    assert l4_008.parse_observations(rows) == [{"date": "2025-09-30", "value": 10.0}]


def test_short_horizons_are_inapplicable():
    result = l4_008.build_output(annual_observations(1))
    assert result["horizons"]["1-5d"]["signal"] == 0
    assert result["horizons"]["1-5d"]["confidence"] == 1


def test_schema_and_insufficient_history():
    result = l4_008.build_output(annual_observations(1))
    assert result["data_frequency"] == "Annual fiscal year"
    assert result["horizons"]["1-3y"]["confidence"] == 0


def test_cache_failure_and_stale(monkeypatch, tmp_path):
    raw = tmp_path / "mts.json"
    raw.write_text(json.dumps({"pages": [{"data": []}]}))
    monkeypatch.setattr(l4_008, "fetch_treasury_table", lambda *args, **kwargs: (_ for _ in ()).throw(TreasuryError("offline")))
    fresh = l4_008.run(raw_path=raw, output_path=tmp_path / "fresh.json")
    assert fresh["horizons"]["1-5d"]["confidence"] == 0
    old = time.time() - 8 * 86400
    os.utime(raw, (old, old))
    stale = l4_008.run(raw_path=raw, output_path=tmp_path / "stale.json")
    assert stale["horizons"]["1-3y"]["confidence"] == 0
    assert "offline" in stale["horizons"]["1-3y"]["evidence"]["summary"]


def test_empty_series_degrades():
    assert l4_008.build_output([])["observation_date"] is None
