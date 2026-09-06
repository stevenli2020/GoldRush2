"""Read current sparse-strategy evidence without collecting or changing signals."""
import json
from pathlib import Path

import yaml

from goldrush2.paths import DR2_CURRENT_DIR, DR3_STRATEGIES_DIR


def render_audit() -> str:
    index = yaml.safe_load((DR3_STRATEGIES_DIR / 'strategies.yaml').read_text())
    configs = [yaml.safe_load((DR3_STRATEGIES_DIR / entry['file']).read_text())
               for entry in index['strategies'] if entry['id'] != 'SP-ALL']
    ids = sorted({vid for config in configs for weights in config['horizon_weights'].values() for vid in weights})
    variables = {vid: json.loads((DR2_CURRENT_DIR / f'{vid}.json').read_text())
                 if (DR2_CURRENT_DIR / f'{vid}.json').exists() else {} for vid in ids}
    lines = ['# Current sparse-input evidence audit', '',
             'Read-only snapshot of stored DR2 evidence; source freshness and source values have not been independently reverified.', '',
             'Confidence denotes the stored extractor field, not a calibrated forecast probability.', '']
    for vid, payload in variables.items():
        lines += [f'## {vid}', '',
                  f"Source: {payload.get('source_name', 'not supplied')} — {payload.get('source_url', 'not supplied')}", '',
                  f"Stored frequency: {payload.get('data_frequency', 'not supplied')}; observation: {payload.get('observation_date', 'not supplied')}", '',
                  '| Horizon | Signal | Confidence | Stored evidence |', '|---|---:|---:|---|']
        for horizon in ('1-5d', '1-3m', '1-3y', '3-10y'):
            item = payload.get('horizons', {}).get(horizon, {})
            evidence = json.dumps(item.get('evidence', {}), ensure_ascii=False).replace('|', '\\|').replace('\n', ' ')
            lines.append(f"| {horizon} | {item.get('signal')} | {item.get('confidence')} | {evidence} |")
        lines.append('')
    lines += ['## Attribution of the current formula', '',
              'These contributions reproduce 100 × weight × signal × confidence for valid inputs. Zero-confidence inputs are hard-gated to zero; configured weight is never redistributed.', '',
              '| Strategy | Horizon | Score | Contributions (points) | Zero-confidence points gated |', '|---|---|---:|---|---:|']
    for config in configs:
        for horizon, weights in config['horizon_weights'].items():
            total = zero_conf = 0
            parts = []
            for vid, weight in weights.items():
                item = variables[vid].get('horizons', {}).get(horizon, {})
                signal = item.get('signal')
                confidence = item.get('confidence')
                contribution = (100 * weight * signal * confidence
                                if isinstance(signal, (int, float)) and -1 <= signal <= 1 and isinstance(confidence, (int, float)) and confidence > 0
                                else 0)
                total += contribution
                if item.get('confidence') == 0:
                    zero_conf += 100 * weight * (signal if isinstance(signal, (int, float)) and -1 <= signal <= 1 else 0)
                parts.append(f'{vid}: {contribution:+.2f}')
            lines.append(f"| {config['strategy']['id']} | {horizon} | {total:.2f} | {'; '.join(parts)} | {zero_conf:+.2f} |")
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    print(render_audit(), end='')
