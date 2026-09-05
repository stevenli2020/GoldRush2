import io
import json
import zipfile
from datetime import date
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from goldrush2.dr2.collectors.cftc import CFTCCollector
from goldrush2.dr2.extractors import l10_001


SAMPLE = (Path(__file__).parent / "fixtures" / "cftc_sample.txt").read_text(encoding="utf-8")


def rows(count=261):
    return [{"date": f"{2020 + i // 52:04d}-{(i % 52) // 4 + 1:02d}-01", "net": i, "open_interest": 400000 + i} for i in range(count)]


def test_collector_parses_current_report():
    parsed = CFTCCollector._parse_report(SAMPLE)
    assert parsed["date"] == "2026-08-25"


def test_collector_extracts_gold_data():
    assert CFTCCollector._parse_report(SAMPLE)["open_interest"] == 427957


def test_collector_extracts_managed_money():
    parsed = CFTCCollector._parse_report(SAMPLE)
    assert parsed["managed_money_long"] == 159819
    assert parsed["managed_money_short"] == 15072


def test_collector_calculates_net():
    assert CFTCCollector._parse_report(SAMPLE)["net"] == 144747


def test_collector_handles_missing_gold():
    with pytest.raises(ValueError, match="does not contain"):
        CFTCCollector._parse_report("other,record\n")


def test_collector_cache_format(tmp_path):
    c = CFTCCollector(tmp_path / "cache", tmp_path / "raw")
    c._save_both([CFTCCollector._parse_report(SAMPLE)])
    assert json.loads((tmp_path / "cache" / "L10-001.json").read_text()) == [{"date": "2026-08-25", "net": 144747}]


def test_collector_historical_archive(monkeypatch, tmp_path):
    c = CFTCCollector(tmp_path / "cache", tmp_path / "raw")
    monkeypatch.setattr(c, "_get", lambda url: SimpleNamespace(content=(lambda b: (lambda z: (z.writestr("data.txt", SAMPLE), z.close(), b.getvalue())[2])(zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED)))(io.BytesIO())))
    assert c._parse_report(c._fetch_historical_report(2025))["date"] == "2026-08-25"


def test_collector_uses_cache(monkeypatch, tmp_path):
    c = CFTCCollector(tmp_path / "cache", tmp_path / "raw")
    c._save_both([{"date": date.today().isoformat(), "net": 1, "open_interest": 2}])
    monkeypatch.setattr(c, "_fetch_current_report", lambda: pytest.fail("cache should be used"))
    assert c.fetch()["L10-002"].exists()


def test_collector_force_refresh(monkeypatch, tmp_path):
    c = CFTCCollector(tmp_path / "cache", tmp_path / "raw")
    c._save_both(rows(2))
    monkeypatch.setattr(c, "_fetch_current_report", lambda: SAMPLE)
    monkeypatch.setattr(c, "_load_history", lambda: [CFTCCollector._parse_report(SAMPLE)])
    c.fetch(force=True)
    assert json.loads(c.l10_001_cache_path.read_text())[0]["net"] == 144747


def test_extractor_signal_rising():
    output = l10_001.build_output(rows())
    assert output["horizons"]["1-5d"]["signal"] == 1


def test_extractor_signal_falling():
    values = [{"date": f"2020-{i // 28 + 1:02d}-{i % 28 + 1:02d}", "net": 300 - i} for i in range(261)]
    assert l10_001.build_output(values)["horizons"]["1-5d"]["signal"] == -1


def test_extractor_signal_unchanged():
    output = l10_001.build_output([{ "date": f"2020-{i // 28 + 1:02d}-{i % 28 + 1:02d}", "net": 3} for i in range(261)])
    assert output["horizons"]["1-5d"]["signal"] == 0


def test_extractor_graded_confidence():
    horizons = l10_001.build_output(rows())["horizons"]
    assert [horizons[key]["confidence"] for key in ("1-5d", "1-3m", "1-3y", "3-10y")] == [1.0, 0.8, 0.6, 0.4]


def test_extractor_insufficient_data():
    result = l10_001.build_output(rows(5))["horizons"]["1-3m"]
    assert result["signal"] == 0 and result["confidence"] == 0.0


def test_extractor_missing_data_gap():
    result = l10_001.build_output(rows(), today="2030-01-01")["horizons"]["1-5d"]
    assert result["signal"] == 0 and result["confidence"] == 0.0


def test_extractor_output_schema():
    output = l10_001.build_output(rows())
    assert output["variable_id"] == "L10-001"
    assert set(output["horizons"]) == {"1-5d", "1-3m", "1-3y", "3-10y"}
