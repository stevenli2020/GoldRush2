import json
from pathlib import Path

from goldrush2.collectors.cftc import CFTCCollector
from goldrush2.extractors import l10_002


def rows(count=261):
    return [{"date": f"{2020 + i // 52:04d}-{(i % 52) // 4 + 1:02d}-01", "open_interest": i} for i in range(count)]


def test_collector_extracts_open_interest():
    text = (Path(__file__).parent / "fixtures" / "cftc_sample.txt").read_text()
    assert CFTCCollector._parse_report(text)["open_interest"] == 427957


def test_collector_cache_format_oi(tmp_path):
    c = CFTCCollector(tmp_path / "cache", tmp_path / "raw")
    c._save_both([{ "date": "2026-08-25", "net": 1, "open_interest": 427957}])
    assert json.loads(c.l10_002_cache_path.read_text()) == [{"date": "2026-08-25", "open_interest": 427957}]


def test_extractor_signal_rising():
    assert l10_002.build_output(rows())["horizons"]["1-5d"]["signal"] == 1


def test_extractor_signal_falling():
    values = [{"date": f"2020-{i // 28 + 1:02d}-{i % 28 + 1:02d}", "open_interest": 300 - i} for i in range(261)]
    assert l10_002.build_output(values)["horizons"]["1-5d"]["signal"] == -1


def test_extractor_signal_unchanged():
    values = [{"date": f"2020-{i // 28 + 1:02d}-{i % 28 + 1:02d}", "open_interest": 3} for i in range(261)]
    assert l10_002.build_output(values)["horizons"]["1-5d"]["signal"] == 0


def test_extractor_graded_confidence():
    horizons = l10_002.build_output(rows())["horizons"]
    assert [horizons[key]["confidence"] for key in ("1-5d", "1-3m", "1-3y", "3-10y")] == [1.0, 0.8, 0.6, 0.4]


def test_extractor_insufficient_data():
    result = l10_002.build_output(rows(5))["horizons"]["1-3m"]
    assert result["signal"] == 0 and result["confidence"] == 0.0


def test_extractor_no_dependency():
    evidence = l10_002.build_output(rows())["horizons"]["1-5d"]["evidence"]
    assert not any(key.startswith("l10_001") for key in evidence)


def test_extractor_output_schema():
    output = l10_002.build_output(rows())
    assert output["data_frequency"] == "Weekly"
    assert set(output["horizons"]) == {"1-5d", "1-3m", "1-3y", "3-10y"}


def test_extractor_writes_atomic_output(tmp_path):
    cache = tmp_path / "cache.json"
    output_path = tmp_path / "current.json"
    cache.write_text(json.dumps(rows()))
    result = l10_002.run(cache_path=cache, output_path=output_path)
    assert output_path.exists() and result["variable_id"] == "L10-002"

