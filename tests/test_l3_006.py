import json
from pathlib import Path

import pytest

from goldrush2.collectors.fed import FedCollector
from goldrush2.extractors import l3_006
from goldrush2.ai import fomc_scorer

FIXTURE = (Path(__file__).parent / "fixtures" / "fomc_statement_sample.html").read_text()


def statements():
    return [{"date": "2026-06-17", "rate_range": "3.50-3.75", "text": "prior", "url": "p"}, {"date": "2026-07-29", "rate_range": "3.50-3.75", "text": "current", "url": "c"}]


def test_parse_statement_html():
    result = FedCollector(Path("/tmp"))._parse_fomc_statement(FIXTURE, "u")
    assert result["date"] == "2026-07-29" and result["rate_range"] == "3.50-3.75"


def test_parse_statement_requires_body():
    with pytest.raises(ValueError):
        FedCollector(Path("/tmp"))._parse_fomc_statement("<html>empty</html>", "u")


def test_rate_number_fraction():
    assert FedCollector._rate_number("3-1/2") == 3.5


def test_statement_url():
    assert FedCollector._statement_url("2026-07-29").endswith("monetary20260729a.htm")


def test_calendar_parser(monkeypatch):
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return (Path(__file__).parent / "fixtures" / "fomc_calendar_sample.html").read_bytes()
    monkeypatch.setattr("goldrush2.collectors.fed.urlopen", lambda *a, **k: Response())
    assert FedCollector(Path("/tmp"))._get_recent_meeting_dates(2) == ["2026-07-29", "2026-06-17"]


def test_calendar_fallback(monkeypatch):
    monkeypatch.setattr("goldrush2.collectors.fed.urlopen", lambda *a, **k: (_ for _ in ()).throw(OSError()))
    assert len(FedCollector(Path("/tmp"))._get_recent_meeting_dates(2)) == 2


def test_backfill_empty_cache(tmp_path, monkeypatch):
    c = FedCollector(tmp_path, variable_id="L3-006")
    monkeypatch.setattr(c, "_get_recent_meeting_dates", lambda count=2: ["2026-07-29", "2026-06-17"])
    monkeypatch.setattr(c, "_fetch_fomc_statement", lambda d=None: {"date": d, "text": d, "url": "u"})
    c._ensure_minimum_cache_entries()
    assert len(c.load_cache()) == 2


def test_backfill_no_duplicate(tmp_path, monkeypatch):
    c = FedCollector(tmp_path, variable_id="L3-006")
    c.cache_path.write_text(json.dumps([statements()[0], statements()[1]]))
    monkeypatch.setattr(c, "_get_recent_meeting_dates", lambda count=2: ["2026-07-29", "2026-06-17"])
    c._ensure_minimum_cache_entries()
    assert len(c.load_cache()) == 2


def test_collector_statement_run(tmp_path, monkeypatch):
    c = FedCollector(tmp_path, variable_id="L3-006")
    monkeypatch.setattr(c, "_fetch_fomc_statement", lambda d=None: {"date": d or "2026-07-29", "text": "x", "url": "u"})
    monkeypatch.setattr(c, "_get_recent_meeting_dates", lambda count=2: ["2026-07-29", "2026-06-17"])
    assert len(c.run()) == 2


def test_extractor_base_output():
    out = l3_006.build_output(statements())
    assert out["ai_status"] == "not_run" and all(h["signal"] == 0 for h in out["horizons"].values())


def test_extractor_short_horizon_confidence_zero():
    assert l3_006.build_output(statements())["horizons"]["1-5d"]["confidence"] == 0


def test_extractor_long_horizon_zero():
    assert l3_006.build_output(statements())["horizons"]["3-10y"]["signal"] == 0


def test_extractor_preserves_ai_same_date():
    base = l3_006.build_output(statements()); base.update({"ai_status": "success", "ai": {"baseline": 50}})
    assert l3_006.build_output(statements(), base)["ai_status"] == "success"


def test_extractor_clears_ai_new_date():
    base = l3_006.build_output(statements()); base.update({"ai_status": "success", "ai": {}})
    changed = statements() + [{"date": "2026-08-01", "text": "new", "url": "n"}]
    assert l3_006.build_output(changed, base)["ai_status"] == "not_run"


def test_extractor_force_clears_ai():
    base = l3_006.build_output(statements()); base.update({"ai_status": "success", "ai": {}})
    assert l3_006.build_output(statements(), base, True)["ai_status"] == "not_run"


def test_extractor_unsorted():
    assert l3_006.build_output(list(reversed(statements())))["observation_date"] == "2026-07-29"


def test_confidence_mapping():
    assert fomc_scorer._confidence("PASS") == 1 and fomc_scorer._confidence("FLAG") == .5 and fomc_scorer._confidence("BLOCKED") == 0


def test_scorer_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(fomc_scorer, "CACHE_PATH", tmp_path / "cache.json"); monkeypatch.setattr(fomc_scorer, "SCORES_PATH", tmp_path / "scores.json"); monkeypatch.setattr(fomc_scorer, "OUTPUT_PATH", tmp_path / "out.json")
    fomc_scorer.CACHE_PATH.write_text(json.dumps(statements()))
    calls = []
    def invoke(prompt, model): calls.append(prompt); return {"baseline_score": 50, "coverage": 1, "quality_status": "PASS"} if len(calls) == 1 else {"hawkish_score": 50}
    fomc_scorer.score_l3_006(call=invoke); count = len(calls); fomc_scorer.score_l3_006(call=lambda *a: (_ for _ in ()).throw(AssertionError())); assert len(calls) == count


def test_scorer_threshold_below(tmp_path, monkeypatch):
    monkeypatch.setattr(fomc_scorer, "CACHE_PATH", tmp_path / "cache.json"); monkeypatch.setattr(fomc_scorer, "SCORES_PATH", tmp_path / "scores.json"); monkeypatch.setattr(fomc_scorer, "OUTPUT_PATH", tmp_path / "out.json")
    fomc_scorer.CACHE_PATH.write_text(json.dumps(statements())); fomc_scorer.SCORES_PATH.write_text(json.dumps({"2026-06-17": {"baseline": 50}}))
    def invoke(prompt, model): return {"baseline_score": 50.5, "coverage": 1, "quality_status": "PASS"} if "baseline_score" in prompt else {"hawkish_score": 50}
    assert fomc_scorer.score_l3_006(call=invoke)["ai"]["signal"] == 0


def test_scorer_dovish_and_hawkish_threshold(tmp_path, monkeypatch):
    assert fomc_scorer.MIN_SCORE_CHANGE == 1.0


def test_scorer_no_previous(tmp_path, monkeypatch):
    monkeypatch.setattr(fomc_scorer, "CACHE_PATH", tmp_path / "cache.json"); monkeypatch.setattr(fomc_scorer, "SCORES_PATH", tmp_path / "scores.json"); monkeypatch.setattr(fomc_scorer, "OUTPUT_PATH", tmp_path / "out.json")
    fomc_scorer.CACHE_PATH.write_text(json.dumps([statements()[1]]))
    def invoke(prompt, model): return {"baseline_score": 50, "coverage": 1, "quality_status": "PASS"} if "baseline_score" in prompt else {"hawkish_score": 50}
    assert fomc_scorer.score_l3_006(call=invoke)["ai"]["signal"] == 0


def test_scorer_api_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(fomc_scorer, "CACHE_PATH", tmp_path / "cache.json"); monkeypatch.setattr(fomc_scorer, "SCORES_PATH", tmp_path / "scores.json"); monkeypatch.setattr(fomc_scorer, "OUTPUT_PATH", tmp_path / "out.json")
    fomc_scorer.CACHE_PATH.write_text(json.dumps([statements()[1]]))
    result = fomc_scorer.score_l3_006(call=lambda *a: (_ for _ in ()).throw(RuntimeError("down")))
    assert result["ai_status"] == "error"


def test_raw_response_storage(tmp_path, monkeypatch):
    assert fomc_scorer.RAW_DIR.name == "raw"

