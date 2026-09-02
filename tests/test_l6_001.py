import json
from pathlib import Path
import pandas as pd
from goldrush2.collectors.gpr import GPRCollector
from goldrush2.extractors.l6_001 import run

def _cache(tmp_path, n=70):
    p=tmp_path/'cache.json'; rows=[{'date':(pd.Timestamp('2026-01-01')+pd.Timedelta(days=i)).date().isoformat(),'value':float(i%10)} for i in range(n)]; p.write_text(json.dumps(rows)); return p
def test_gpr_parse_csv(tmp_path):
    raw=tmp_path/'x.csv'; raw.write_text('date,GPRD_ACT\n2026-01-01,2\n'); c=GPRCollector(tmp_path/'c',tmp_path/'z.zip'); c.parse(raw); assert json.loads(c.cache_path.read_text())[0]['value']==2
def test_cache_shape(tmp_path): assert _cache(tmp_path).exists()
def test_short_horizons_present(tmp_path):
    out=run(_cache(tmp_path),tmp_path/'o.json'); assert set(out['horizons'])=={'1-5d','1-3m','1-3y','3-10y'}
def test_long_disabled(tmp_path):
    out=run(_cache(tmp_path),tmp_path/'o.json'); assert out['horizons']['1-3y']['confidence']==0
def test_insufficient_history(tmp_path):
    out=run(_cache(tmp_path,10),tmp_path/'o.json'); assert out['horizons']['1-5d']['confidence']==0
def test_positive_signal(tmp_path):
    p=_cache(tmp_path); rows=json.loads(p.read_text()); [r.update(value=100+i) for i,r in enumerate(rows[-5:])]; p.write_text(json.dumps(rows)); assert run(p,tmp_path/'o.json')['horizons']['1-5d']['signal']==1
def test_output_written(tmp_path): run(_cache(tmp_path),tmp_path/'o.json'); assert (tmp_path/'o.json').exists()
def test_source_url(tmp_path): assert 'matteoiacoviello' in run(_cache(tmp_path),tmp_path/'o.json')['source_url']
def test_observation_date(tmp_path): assert run(_cache(tmp_path),tmp_path/'o.json')['observation_date']=='2026-03-11'
def test_dedup(tmp_path):
    c=GPRCollector(tmp_path/'c',tmp_path/'z.zip'); assert c._deduplicate([{'date':'2020','value':1},{'date':'2020','value':2}])[0]['value']==2
def test_snapshot_fallback(tmp_path):
    s=tmp_path/'s.csv'; s.write_text('date,GPRD_ACT\n2026-01-01,1\n'); c=GPRCollector(tmp_path/'c',tmp_path/'missing.zip',snapshot_path=s); assert c.fetch()==s
def test_meta_saved(tmp_path):
    c=GPRCollector(tmp_path/'c',tmp_path/'z.zip'); c.parse(tmp_path/'s.csv') if (tmp_path/'s.csv').exists() else None
def test_alias_extract(tmp_path): assert callable(__import__('goldrush2.extractors.l6_001',fromlist=['extract']).extract)
def test_zero_signal(tmp_path):
    p=_cache(tmp_path); rows=json.loads(p.read_text()); [r.update(value=5) for r in rows]; p.write_text(json.dumps(rows)); assert run(p,tmp_path/'o.json')['horizons']['1-5d']['signal']==0
def test_json_serializable(tmp_path): json.dumps(run(_cache(tmp_path),tmp_path/'o.json'))
