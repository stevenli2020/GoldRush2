from datetime import date
import json

import pytest

from goldrush2.dr2.collectors import cme_futures
from goldrush2.dr2.collectors.cme_futures import CMEFuturesCollector, align_contract_prices, apply_sofr, get_contract_symbol, get_near_and_far_contracts


@pytest.mark.parametrize("month,code", [(1, "F"), (2, "G"), (3, "H"), (4, "J"), (5, "K"), (6, "M"), (7, "N"), (8, "Q"), (9, "U"), (10, "V"), (11, "X"), (12, "Z")])
def test_contract_symbol_generation(month, code):
    assert get_contract_symbol(2026, month) == f"GC{code}26.CMX"


def test_dynamic_near_and_far_contract_selection():
    near, far, days = get_near_and_far_contracts(date(2026, 9, 2))
    assert (near, far, days) == ("GCV26.CMX", "GCZ26.CMX", 61)


def test_contract_selection_skips_expired_delivery_month():
    near, far, _days = get_near_and_far_contracts(date(2026, 12, 31))
    assert (near, far) == ("GCG27.CMX", "GCJ27.CMX")


def test_align_contract_prices_uses_inner_join():
    rows = align_contract_prices(
        {"2026-08-28": 3400.0, "2026-09-01": 3410.0},
        {"2026-09-01": 3450.0, "2026-09-02": 3460.0},
        near_contract="GCV26.CMX",
        far_contract="GCZ26.CMX",
        days_between=61,
    )
    assert rows == [{"date": "2026-09-01", "near": 3410.0, "far": 3450.0, "near_contract": "GCV26.CMX", "far_contract": "GCZ26.CMX", "days_between": 61}]


def test_apply_sofr_forward_fills_missing_sofr_date():
    rows = apply_sofr(
        [{"date": "2026-09-01", "near": 3400.0, "far": 3450.0, "near_contract": "GCV26.CMX", "far_contract": "GCZ26.CMX", "days_between": 61}],
        [{"date": "2026-08-31", "value": 4.0}],
    )
    assert rows[0]["sofr"] == 4.0
    assert rows[0]["sofr_is_filled"] is True


def test_apply_sofr_calculates_proxy():
    rows = apply_sofr(
        [{"date": "2026-09-01", "near": 3400.0, "far": 3450.0, "near_contract": "GCV26.CMX", "far_contract": "GCZ26.CMX", "days_between": 61}],
        [{"date": "2026-09-01", "value": 4.0}],
    )
    assert rows[0]["value"] == pytest.approx(rows[0]["sofr"] - rows[0]["forward_rate"])


def test_collector_downloads_specific_contract_pair(monkeypatch, tmp_path):
    collector = CMEFuturesCollector(tmp_path / "cache", tmp_path / "gold_futures_pair.json", tmp_path / "SOFR.json")
    monkeypatch.setattr(cme_futures, "get_near_and_far_contracts", lambda: ("GCV26.CMX", "GCZ26.CMX", 61))
    monkeypatch.setattr(cme_futures, "_download_contract", lambda symbol, **_kwargs: {"2026-09-01": 3400.0 if symbol == "GCV26.CMX" else 3450.0})
    monkeypatch.setattr(cme_futures, "fetch_series", lambda *_args, **_kwargs: [{"date": "2026-09-01", "value": 4.0}])
    rows = collector.download_full()
    assert rows[0]["near_contract"] == "GCV26.CMX"
    assert json.loads(collector.raw_path.read_text())["far_contract"] == "GCZ26.CMX"


def test_collector_latest_date_uses_near_contract(monkeypatch, tmp_path):
    collector = CMEFuturesCollector(tmp_path / "cache", tmp_path / "gold_futures_pair.json", tmp_path / "SOFR.json")
    monkeypatch.setattr(cme_futures, "get_near_and_far_contracts", lambda: ("GCV26.CMX", "GCZ26.CMX", 61))
    monkeypatch.setattr(cme_futures, "_download_contract", lambda *_args, **_kwargs: {"2026-08-28": 3400.0, "2026-09-01": 3410.0})
    assert collector.fetch_latest_observation_date() == "2026-09-01"
