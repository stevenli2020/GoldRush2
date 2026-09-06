import json
import shutil

import pytest

from goldrush2.dr3.analytics.multi_strategy import StrategyValidationError, _current_signal, _validate_weights, load_strategy_set, run_multi_strategy
from goldrush2.dr3.analytics.score_delta_report import render_report
from goldrush2.paths import DR3_STRATEGIES_DIR
from goldrush2.dr3.analytics.models import VariableResult


def test_comparison_command_preserves_weights_inputs_and_official_output(tmp_path, monkeypatch):
    from goldrush2 import cli, paths
    from goldrush2.dr3.analytics import aggregator, multi_strategy

    configs = tmp_path / 'strategies'
    shutil.copytree(DR3_STRATEGIES_DIR, configs)
    inputs = tmp_path / 'inputs'
    inputs.mkdir()
    (inputs / 'L1-001.json').write_text(json.dumps({
        'variable_id': 'L1-001', 'horizons': {
            h: {'signal': -1, 'confidence': 0.4, 'evidence': {'data': {}}}
            for h in ('1-5d', '1-3m', '1-3y', '3-10y')}}))
    official = tmp_path / 'current_scores.json'
    official.write_bytes(b'{"official_sentinel": true}\n')
    comparison = tmp_path / 'comparison.json'
    protected = [*configs.glob('*.yaml'), *inputs.glob('*.json'), official]
    before = {path: path.read_bytes() for path in protected}
    # Redirect IO defaults only; exercise the real CLI dispatch, loader and scorer.
    monkeypatch.setattr(multi_strategy.run_multi_strategy, '__defaults__', (configs, comparison, inputs))
    monkeypatch.setattr(paths, 'DR3_SCORES_PATH', official)
    monkeypatch.setattr(aggregator, 'SCORES_OUTPUT_FILE', official)
    assert cli.main(['analyze-strategies']) == 0
    assert {path: path.read_bytes() for path in protected} == before
    output = json.loads(comparison.read_text())
    assert output['official_strategy'] is None
    assert len(output['strategies']) == 15
    for h in output['strategies']['SP-RATE']['horizons'].values():
        assert h['score'] == -24
        assert h['usable_weight_coverage'] == 0.6
        assert h['status'] == 'DEGRADED'


def test_cancellation_is_distinct_from_no_usable_data(tmp_path):
    empty = run_multi_strategy(data_dir=tmp_path, output_path=tmp_path / 'empty.json')
    for vid, signal in [('L1-001', 1), ('L2-001', -1)]:
        (tmp_path / f'{vid}.json').write_text(json.dumps({
            'variable_id': vid, 'horizons': {
                h: {'signal': signal, 'confidence': 1, 'evidence': {'data': {}}}
                for h in ('1-5d', '1-3m', '1-3y', '3-10y')}}))
    result = run_multi_strategy(data_dir=tmp_path, output_path=tmp_path / 'mixed.json')
    # SP-SPARSE gives each input 10%; cancellation is known neutrality at 20% coverage.
    for h in ('1-5d', '1-3m', '1-3y', '3-10y'):
        missing = empty['strategies']['SP-SPARSE']['horizons'][h]
        mixed = result['strategies']['SP-SPARSE']['horizons'][h]
        assert missing['score'] == mixed['score'] == 0
        assert missing['usable_weight_coverage'] == 0
        assert mixed['usable_weight_coverage'] == 0.2
        assert mixed['contributions']['L1-001']['contribution'] == 10
        assert mixed['contributions']['L2-001']['contribution'] == -10


def test_missing_horizon_invalid_file_and_valid_neutral(tmp_path, capsys):
    (tmp_path / 'L1-001.json').write_text('{broken json')
    (tmp_path / 'L2-001.json').write_text(json.dumps({'variable_id': 'L2-001', 'horizons': {}}))
    (tmp_path / 'L4-001.json').write_text(json.dumps({'variable_id': 'L4-001', 'horizons': {
        '1-5d': {'signal': 0, 'confidence': 1, 'evidence': {'data': {}}}}}))
    result = run_multi_strategy(data_dir=tmp_path, output_path=tmp_path / 'result.json')
    horizon = result['strategies']['SP-RATE']['horizons']['1-5d']
    assert horizon['score'] == 0
    assert horizon['usable_weight_coverage'] == 0.15
    assert horizon['contributions']['L4-001']['input_status'] == 'VALID'
    for vid in ('L1-001', 'L2-001'):
        assert horizon['contributions'][vid]['input_status'] == 'MISSING'
        assert horizon['contributions'][vid]['contribution'] == 0
        assert any(vid in warning for warning in horizon['warnings'])
    assert 'Failed to parse L1-001.json' in capsys.readouterr().err


@pytest.mark.parametrize('signal,confidence,applicable,expected,warning', [
    (1, 0, None, 0, 'zero confidence'),
    (-1, 0, None, 0, 'zero confidence'),
    (1, 0.4, None, 1, ''),
    (-1, 1, None, -1, ''),
    (0, 1, None, 0, ''),
    (1, 1, False, 0, 'INAPPLICABLE'),
    (None, 1, None, 0, 'INVALID SIGNAL'),
    ([], 1, None, 0, 'INVALID SIGNAL'),
    (True, 1, None, 0, 'INVALID SIGNAL'),
    (2, 1, None, 0, 'INVALID SIGNAL'),
    (1, float('nan'), None, 0, 'INVALID CONFIDENCE'),
    (1, None, None, 0, 'INVALID CONFIDENCE'),
    (1, 2, None, 0, 'INVALID CONFIDENCE'),
])
def test_input_gate(signal, confidence, applicable, expected, warning, capsys):
    variable = VariableResult.from_dict({'variable_id': 'L6-001', 'horizons': {
        '1-5d': {'signal': signal, 'confidence': confidence,
                 'evidence': {'data': {'applicable': applicable}}}}})
    assert _current_signal({'L6-001': variable}, 'L6-001', '1-5d') == expected
    stderr = capsys.readouterr().err
    assert warning in stderr if warning else not stderr


def test_fixed_weight_scoring_with_unusable_input(tmp_path):
    # SP-RATE has 60% real yields and 10% dollar. Stale yields must not
    # contribute; fractional dollar confidence linearly decays its 10 points.
    for vid, confidence in [('L1-001', 0), ('L2-001', 0.4)]:
        payload = {'variable_id': vid, 'horizons': {
            h: {'signal': 1, 'confidence': confidence, 'evidence': {'data': {}}}
            for h in ('1-5d', '1-3m', '1-3y', '3-10y')}}
        (tmp_path / f'{vid}.json').write_text(json.dumps(payload))
    result = run_multi_strategy(data_dir=tmp_path, output_path=tmp_path / 'result.json')
    assert all(h['score'] == 4 for h in result['strategies']['SP-RATE']['horizons'].values())


def test_structured_contributions_and_coverage(tmp_path):
    cases = {
        'L1-001': (1, 0, {}, 'Cached data is stale'),
        'L2-001': (-1, 0.4, {}, ''),
        'L4-001': (0, 1, {}, ''),
        'L5-001': (1, 1, {'applicable': False}, ''),
        'L7-001': (None, 1, {}, ''),
    }
    for vid, (signal, confidence, data, warning) in cases.items():
        (tmp_path / f'{vid}.json').write_text(json.dumps({
            'variable_id': vid, 'horizons': {
                h: {'signal': signal, 'confidence': confidence,
                    'evidence': {'data': data, 'warning': warning}}
                for h in ('1-5d', '1-3m', '1-3y', '3-10y')}}))
    result = run_multi_strategy(data_dir=tmp_path, output_path=tmp_path / 'result.json')
    horizon = result['strategies']['SP-RATE']['horizons']['1-5d']
    assert horizon['score'] == -4
    assert horizon['usable_weight_coverage'] == 0.25  # valid dollar and neutral CPI
    entries = horizon['contributions']
    assert {vid: item['input_status'] for vid, item in entries.items()} == {
        'L1-001': 'STALE', 'L2-001': 'VALID', 'L4-001': 'VALID',
        'L5-001': 'INAPPLICABLE', 'L7-001': 'INVALID', 'L8-001': 'MISSING'}
    assert entries['L1-001']['signal'] == 1
    assert entries['L1-001']['contribution'] == 0
    assert entries['L2-001']['confidence'] == 0.4
    assert entries['L2-001']['contribution'] == -4
    assert any('Cached data is stale' in warning for warning in horizon['warnings'])
    for strategy in result['strategies'].values():
        assert len(strategy['horizons']) == 4
        for output in strategy['horizons'].values():
            assert output['score'] == pytest.approx(sum(e['contribution'] for e in output['contributions'].values()), abs=1e-6)


def test_coverage_threshold_and_strategy_status(tmp_path):
    for vid in ('L1-001', 'L2-001'):
        (tmp_path / f'{vid}.json').write_text(json.dumps({
            'variable_id': vid, 'horizons': {
                h: {'signal': 1, 'confidence': 1, 'evidence': {'data': {}}}
                for h in ('1-5d', '1-3m', '1-3y', '3-10y')}}))
    result = run_multi_strategy(data_dir=tmp_path, output_path=tmp_path / 'result.json')
    rate = result['strategies']['SP-RATE']
    # SP-RATE's two valid inputs cover exactly 70%, the approved validity floor.
    assert all(h['usable_weight_coverage'] == 0.7 and h['status'] == 'VALID' for h in rate['horizons'].values())
    assert rate['status'] == 'VALID'
    assert result['strategies']['SP-CB']['status'] == 'DEGRADED'


def test_score_delta_report_covers_each_frozen_strategy_horizon(tmp_path):
    comparison_path = tmp_path / 'comparison.json'
    run_multi_strategy(data_dir=tmp_path, output_path=comparison_path)
    report = render_report(comparison_path)
    assert report.count('| SP-RATE |') == 4
    assert '| SP-L6L7 | 1-5d | +10.0 | +0.0 | -10.0 | 0% | DEGRADED |' in report
    assert '60 of 60 strategy-horizon results are DEGRADED' in report


def test_strategy_set_contains_the_frozen_fifteen_configs():
    strategies = load_strategy_set()
    assert len(strategies) == 15
    assert [item["config"]["strategy"]["id"] for item in strategies][-1] == "SP-ALL"
    short = next(item["config"] for item in strategies if item["config"]["strategy"]["id"] == "SP-SHORT")
    assert short["horizon_weights"]["1-3y"]["L8-001"] == 0.25


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ("L1-001: 0.61", "weights sum"),
        ("L1-001", "unknown variables"),
    ],
)
def test_invalid_strategy_config_hard_fails(tmp_path, replacement, message):
    strategies_dir = tmp_path / "strategies"
    shutil.copytree(DR3_STRATEGIES_DIR, strategies_dir)
    rate_path = strategies_dir / "weights_strategy_SP-RATE.yaml"
    text = rate_path.read_text(encoding="utf-8")
    if replacement == "L1-001: 0.61":
        text = text.replace("L1-001: 0.60", replacement)
    else:
        text = text.replace("L1-001", "L99-999")
    rate_path.write_text(text, encoding="utf-8")
    with pytest.raises(StrategyValidationError, match=message):
        load_strategy_set(strategies_dir)


def test_missing_horizon_hard_fails(tmp_path):
    strategies_dir = tmp_path / "strategies"
    shutil.copytree(DR3_STRATEGIES_DIR, strategies_dir)
    rate_path = strategies_dir / "weights_strategy_SP-RATE.yaml"
    text = rate_path.read_text(encoding="utf-8").replace("  3-10y: *rate\n", "")
    rate_path.write_text(text, encoding="utf-8")
    with pytest.raises(StrategyValidationError, match="horizon weights"):
        load_strategy_set(strategies_dir)


def test_negative_weight_and_excess_active_variables_hard_fail():
    known = {f"L0-{index:03d}" for index in range(1, 18)}
    weights = {horizon: {"L0-001": 1.0} for horizon in ("1-5d", "1-3m", "1-3y", "3-10y")}
    weights["1-5d"]["L0-001"] = -0.1
    with pytest.raises(StrategyValidationError, match="negative"):
        _validate_weights(weights, "TEST", known, 0.001, 15)

    weights["1-5d"] = {f"L0-{index:03d}": 1 / 16 for index in range(1, 17)}
    with pytest.raises(StrategyValidationError, match="exceeds 15"):
        _validate_weights(weights, "TEST", known, 0.001, 15)


def test_missing_current_signal_is_neutral_without_weight_renormalization():
    assert _current_signal({}, "L1-001", "1-5d") == 0


def test_multi_strategy_output_is_current_only_and_non_official(tmp_path):
    output_path = tmp_path / "dr3_multi_strategy_outlook.json"
    result = run_multi_strategy(data_dir=tmp_path, output_path=output_path)
    persisted = json.loads(output_path.read_text(encoding="utf-8"))
    assert result == persisted
    assert result["mode"] == "current_outlook_only"
    assert result["official_strategy"] is None
    from goldrush2.dr3.analytics.multi_strategy import production_variable_ids
    assert result["admit_variable_count"] == len(production_variable_ids())
    assert len(result["strategies"]) == 15
    assert set(result["strategies"]["SP-RATE"]["horizons"]) == {"1-5d", "1-3m", "1-3y", "3-10y"}
    assert result["strategies"]["SP-TECH"]["production_eligible"] is False
    assert result["strategies"]["SP-ALL"]["production_eligible"] is False
    assert result["strategies"]["SP-ALL"]["horizons"]["1-5d"]["active_variables"] == "AUTO_UNIFORM_ADMIT"
    for strategy in result['strategies'].values():
        assert set(strategy['horizons']) == {'1-5d', '1-3m', '1-3y', '3-10y'}
    assert set(result['strategies']['SP-ALL']['horizons']['1-5d']['contributions']) == production_variable_ids()
