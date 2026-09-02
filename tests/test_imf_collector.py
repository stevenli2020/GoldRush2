import pytest

from goldrush2.collectors.imf import IMFCollector, parse_csv, quarter_end


HEADER = "STRUCTURE_ID,COUNTRY,INDICATOR,FXR_CURRENCY,TYPE_OF_TRANSFORMATION,FREQUENCY,TIME_PERIOD,OBS_VALUE\n"


def csv_bytes(rows):
    return (HEADER + "\n".join(f"IMF.STA:COFER(7.0.1),{country},AFXRA,{currency},SHRO_PT,{freq},{period},{value}" for country, currency, freq, period, value in rows) + "\n").encode()


def test_quarter_end():
    assert quarter_end("2025-Q1") == "2025-03-31"
    assert quarter_end("2025-Q2") == "2025-06-30"


def test_parse_filters_dimensions():
    data = csv_bytes([("G001", "CI_USD", "Q", "2024-Q1", 58), ("G002", "CI_USD", "Q", "2024-Q2", 57), ("G001", "CI_USD", "A", "2024", 59)])
    assert parse_csv(data) == [{"date": "2024-03-31", "value": 58.0}]


@pytest.mark.parametrize("value", ["", ".", "nan", "inf", "-1", "101", "abc"])
def test_invalid_share_rejected(value):
    with pytest.raises(ValueError):
        parse_csv(csv_bytes([("G001", "CI_USD", "Q", "2024-Q1", value)]))


def test_duplicate_rejected():
    with pytest.raises(ValueError, match="conflicting duplicate"):
        parse_csv(csv_bytes([("G001", "CI_USD", "Q", "2024-Q1", 58), ("G001", "CI_USD", "Q", "2024-Q1", 59)]))


def test_structure_rejected():
    with pytest.raises(ValueError, match="structure"):
        parse_csv(csv_bytes([("G001", "CI_USD", "Q", "2024-Q1", 58)]).replace(b"IMF.STA:COFER", b"BAD"))


def test_collector_full_download(monkeypatch, tmp_path):
    collector = IMFCollector(tmp_path / "cache", tmp_path / "raw" / "cofer.csv")
    monkeypatch.setattr(collector, "_fetch", lambda: csv_bytes([("G001", "CI_USD", "Q", "2024-Q1", 58)]))
    assert collector.download_full() == [{"date": "2024-03-31", "value": 58.0}]
    assert collector.raw_path.exists()


def test_collector_incremental_unsupported(tmp_path):
    with pytest.raises(NotImplementedError):
        IMFCollector(tmp_path / "cache", tmp_path / "raw.csv").download_incremental("2024-03-31")


def test_latest_date(monkeypatch, tmp_path):
    collector = IMFCollector(tmp_path / "cache", tmp_path / "raw.csv")
    monkeypatch.setattr(collector, "_fetch", lambda: csv_bytes([("G001", "CI_USD", "Q", "2024-Q1", 58), ("G001", "CI_USD", "Q", "2025-Q4", 57)]))
    assert collector.fetch_latest_observation_date() == "2025-12-31"
