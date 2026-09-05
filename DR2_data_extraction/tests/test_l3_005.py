import json
from pathlib import Path

import pytest

from goldrush2.dr2.collectors.fed import FedCollector, _release_date, candidate_urls, parse_sep_html
from goldrush2.dr2.extractors import l3_005


FIXTURE = Path(__file__).parent / "fixtures" / "l3_005_sample.html"


def rows():
    return [
        {"date": "2021-09-16", "value": 2.0, "source_url": "u"},
        {"date": "2022-09-16", "value": 2.5, "source_url": "u"},
        {"date": "2025-09-16", "value": 3.5, "source_url": "u"},
        {"date": "2026-09-16", "value": 3.25, "source_url": "u"},
    ]


def test_release_date():
    assert _release_date("https://x/fomcprojtabl20260916.htm") == "2026-09-16"


def test_candidate_urls_have_recent_releases(monkeypatch):
    monkeypatch.setattr("goldrush2.dr2.collectors.fed.urlopen", lambda *a, **k: (_ for _ in ()).throw(OSError()))
    assert any("fomcprojtabl2026" in url for url in candidate_urls(__import__("datetime").date(2026, 9, 1)))


def test_parse_sample_html():
    result = parse_sep_html(FIXTURE.read_bytes(), "2026-09-16", "u")
    assert result["value"] == 3.25 and result["source_url"] == "u"


def test_parse_missing_median_raises():
    with pytest.raises(ValueError):
        parse_sep_html(b"<table><tr><td>Other</td><td>1</td></tr></table>", "2026-09-16", "u")


def test_collector_paths(tmp_path):
    collector = FedCollector(tmp_path)
    assert collector.cache_path.name == "L3-005.json"


def test_collector_appends_without_duplicate(tmp_path, monkeypatch):
    collector = FedCollector(tmp_path)
    collector.cache_path.write_text(json.dumps([{"date": "2025-09-17", "value": 3.5}]))
    monkeypatch.setattr(collector, "_fetch_latest", lambda: {"date": "2026-09-16", "value": 3.25})
    result = collector.run()
    assert [r["date"] for r in result] == ["2025-09-17", "2026-09-16"]
    result = collector.run()
    assert len(result) == 2


def test_collector_snapshot_fallback(tmp_path, monkeypatch):
    snapshot = tmp_path / "snapshot.html"
    snapshot.write_bytes(FIXTURE.read_bytes())
    collector = FedCollector(tmp_path, snapshot_path=snapshot)
    monkeypatch.setattr("goldrush2.dr2.collectors.fed.candidate_urls", lambda: ["https://x/fomcprojtabl20260916.htm"])
    monkeypatch.setattr("goldrush2.dr2.collectors.fed.urlopen", lambda *a, **k: (_ for _ in ()).throw(OSError()))
    assert collector.fetch_latest_observation_date() == "2026-06-17"


def test_short_horizons():
    output = l3_005.build_output(rows())
    assert output["horizons"]["1-5d"]["signal"] == 0
    assert output["horizons"]["1-3m"]["confidence"] == 1


def test_one_year_falling_is_bullish():
    output = l3_005.build_output(rows())
    assert output["horizons"]["1-3y"]["signal"] == 1


def test_five_year_rising_is_bearish():
    output = l3_005.build_output(rows())
    assert output["horizons"]["3-10y"]["signal"] == -1


def test_unchanged_is_neutral():
    data = rows(); data[-1]["value"] = 3.5
    assert l3_005.build_output(data)["horizons"]["1-3y"]["signal"] == 0


def test_missing_one_year_lag():
    data = [r for r in rows() if r["date"] != "2025-09-16"]
    result = l3_005.build_output(data)["horizons"]["1-3y"]
    assert result["signal"] is None and result["confidence"] == 0


def test_missing_five_year_lag():
    data = [r for r in rows() if r["date"] != "2021-09-16"]
    result = l3_005.build_output(data)["horizons"]["3-10y"]
    assert result["signal"] is None and result["confidence"] == 0


def test_unsorted_cache_is_sorted():
    output = l3_005.build_output(list(reversed(rows())))
    assert output["observation_date"] == "2026-09-16"


def test_exact_date_not_positional():
    data = rows() + [{"date": "2024-01-01", "value": 9}]
    result = l3_005.build_output(data)["horizons"]["1-3y"]
    assert result["signal"] == 1


def test_output_schema_and_source_url():
    output = l3_005.build_output(rows())
    assert set(("variable_id", "data_frequency", "source_name", "source_url", "observation_date", "horizons")) <= output.keys()
    assert output["source_url"] == "u"


def test_run_writes_output(tmp_path):
    cache = tmp_path / "cache.json"; out = tmp_path / "out.json"
    cache.write_text(json.dumps(rows()))
    result = l3_005.run(cache, out)
    assert json.loads(out.read_text())["variable_id"] == "L3-005"
    assert result["observation_date"] == "2026-09-16"
