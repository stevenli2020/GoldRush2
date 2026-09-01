import json
import os
import time
from datetime import date

import pytest

from goldrush2.collectors.treasury import TreasuryError
from goldrush2.extractors import l4_009


def monthly_observations(count=61, comparison_index=None, current=20.0, comparison=18.0):
    rows = [{"date": f"{2020 + i // 12:04d}-{i % 12 + 1:02d}-01", "value": 18.0} for i in range(count)]
    if comparison_index is not None:
        rows[comparison_index]["value"] = comparison
    rows[-1]["value"] = current
    return rows


@pytest.mark.parametrize("horizon, lookback", [("1-5d", 1), ("1-3m", 3), ("1-3y", 12), ("3-10y", 60)])
@pytest.mark.parametrize("current, comparison, signal", [(20.0, 18.0, 1), (16.0, 18.0, -1), (18.0, 18.0, 0)])
def test_monthly_signal_directions(horizon, lookback, current, comparison, signal):
    result = l4_009.build_output(monthly_observations(comparison_index=61 - 1 - lookback, current=current, comparison=comparison))
    assert result["horizons"][horizon]["signal"] == signal
    assert result["horizons"][horizon]["confidence"] == 1


def test_parse_maturity_ratio():
    rows = [{"record_date": "2026-01-01", "security_type_desc": "Total Marketable", "security_class1_desc": "", "maturity_date": "", "outstanding_amt": "1,000"}, {"record_date": "2026-01-01", "security_type_desc": "Bill", "security_class1_desc": "", "maturity_date": "2026-06-01", "outstanding_amt": "100"}, {"record_date": "2026-01-01", "security_type_desc": "Note", "security_class1_desc": "", "maturity_date": "2028-01-01", "outstanding_amt": "100"}]
    assert l4_009.parse_observations(rows) == [{"date": "2026-01-01", "value": 10.0}]


def test_excludes_matured_and_summary_rows():
    rows = [{"record_date": "2026-01-01", "security_type_desc": "Total Marketable", "maturity_date": "", "outstanding_amt": "1,000"}, {"record_date": "2026-01-01", "security_type_desc": "Summary", "maturity_date": "2026-02-01", "outstanding_amt": "100"}, {"record_date": "2026-01-01", "security_type_desc": "Bill", "maturity_date": "2025-12-01", "outstanding_amt": "100"}]
    assert l4_009.parse_observations(rows) == [{"date": "2026-01-01", "value": 0.0}]


def test_schema_and_insufficient_history():
    result = l4_009.build_output(monthly_observations(3))
    assert result["data_frequency"] == "Monthly"
    assert result["horizons"]["3-10y"]["confidence"] == 0


def test_cache_failure_and_stale(monkeypatch, tmp_path):
    raw = tmp_path / "mspd.json"
    raw.write_text(json.dumps({"pages": [{"data": []}]}))
    monkeypatch.setattr(l4_009, "fetch_treasury_table", lambda *args, **kwargs: (_ for _ in ()).throw(TreasuryError("offline")))
    fresh = l4_009.run(raw_path=raw, output_path=tmp_path / "fresh.json")
    assert fresh["horizons"]["1-5d"]["confidence"] == 0
    old = time.time() - 8 * 86400
    os.utime(raw, (old, old))
    stale = l4_009.run(raw_path=raw, output_path=tmp_path / "stale.json")
    assert "offline" in stale["horizons"]["1-5d"]["evidence"]["summary"]


def test_empty_series_degrades():
    assert l4_009.build_output([])["observation_date"] is None
