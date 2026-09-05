from io import BytesIO
from urllib.error import URLError

import pytest

from goldrush2.dr2.collectors import frb_tips


CSV_TEXT = """Notes about the staff research product
TIPS Yields
Date,TIPSY02,TIPSY05,TIPSY10
2026-08-25,1.50,2.00,2.30
2026-08-26,NA,2.10,2.40
2026-08-27,1.60,2.20,2.50
"""


class FakeResponse:
    def __init__(self, content: bytes):
        self.content = content

    def __enter__(self):
        return BytesIO(self.content)

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_parse_tips_yield_extracts_requested_maturity_and_skips_missing():
    assert frb_tips.parse_tips_yield(CSV_TEXT, "2Y") == [
        {"date": "2026-08-25", "value": 1.5},
        {"date": "2026-08-27", "value": 1.6},
    ]
    assert frb_tips.parse_tips_yield(CSV_TEXT, "5y")[-1]["value"] == 2.2


@pytest.mark.parametrize("maturity", ["1Y", "bad", ""])
def test_parse_tips_yield_rejects_unavailable_or_invalid_maturity(maturity):
    with pytest.raises(frb_tips.FrbTipsDataError):
        frb_tips.parse_tips_yield(CSV_TEXT, maturity)


@pytest.mark.parametrize(
    "csv_text",
    [
        "not the expected file",
        "Date,TIPSY02\nnot-a-date,1.2\n",
        "Date,TIPSY02\n2026-08-27,NaN\n",
    ],
)
def test_parse_tips_yield_rejects_malformed_data(csv_text):
    with pytest.raises(frb_tips.FrbTipsDataError):
        frb_tips.parse_tips_yield(csv_text, "2Y")


def test_fetch_tips_yield_writes_full_raw_csv(monkeypatch, tmp_path):
    content = CSV_TEXT.encode("utf-8")
    monkeypatch.setattr(
        frb_tips, "urlopen", lambda url, timeout: FakeResponse(content)
    )
    raw_path = tmp_path / "real_yield_curve.csv"

    observations = frb_tips.fetch_tips_yield("2Y", raw_path=raw_path)

    assert observations[-1] == {"date": "2026-08-27", "value": 1.6}
    assert raw_path.read_bytes() == content


def test_failed_request_does_not_overwrite_raw_cache(monkeypatch, tmp_path):
    raw_path = tmp_path / "real_yield_curve.csv"
    raw_path.write_text("preserved\n", encoding="utf-8")
    monkeypatch.setattr(
        frb_tips,
        "urlopen",
        lambda url, timeout: (_ for _ in ()).throw(URLError("offline")),
    )

    with pytest.raises(frb_tips.FrbTipsNetworkError, match="offline"):
        frb_tips.fetch_tips_yield("2Y", raw_path=raw_path)

    assert raw_path.read_text(encoding="utf-8") == "preserved\n"


def test_malformed_response_does_not_overwrite_raw_cache(monkeypatch, tmp_path):
    raw_path = tmp_path / "real_yield_curve.csv"
    raw_path.write_text("preserved\n", encoding="utf-8")
    monkeypatch.setattr(
        frb_tips,
        "urlopen",
        lambda url, timeout: FakeResponse(b"unexpected response"),
    )

    with pytest.raises(frb_tips.FrbTipsDataError):
        frb_tips.fetch_tips_yield("2Y", raw_path=raw_path)

    assert raw_path.read_text(encoding="utf-8") == "preserved\n"
