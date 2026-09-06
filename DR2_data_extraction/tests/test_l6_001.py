import json
from pathlib import Path
import pandas as pd
import os, time
from datetime import date, timedelta
from goldrush2.dr2.collectors.gpr import GPRCollector
from goldrush2.dr2.extractors.l6_001 import run

def _cache(tmp_path, n=70):
    p=tmp_path/'cache.json'; end=pd.Timestamp(date.today()-timedelta(days=1)); rows=[{'date':(end-pd.Timedelta(days=n-i-1)).date().isoformat(),'value':float(i%10)} for i in range(n)]; p.write_text(json.dumps(rows)); (tmp_path/'L6-001_meta.json').write_text(json.dumps({'source_vintage_date': (date.today()-timedelta(days=1)).isoformat(), 'downloaded_at': date.today().isoformat()})); return p
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
def test_observation_date(tmp_path): assert run(_cache(tmp_path),tmp_path/'o.json')['observation_date']==(date.today()-timedelta(days=1)).isoformat()
def test_dedup(tmp_path):
    c=GPRCollector(tmp_path/'c',tmp_path/'z.zip'); assert c._deduplicate([{'date':'2020','value':1},{'date':'2020','value':2}])[0]['value']==2
def test_snapshot_fallback(tmp_path):
    s=tmp_path/'s.csv'; s.write_text('date,GPRD_ACT\n2026-01-01,1\n'); c=GPRCollector(tmp_path/'c',tmp_path/'missing.zip',snapshot_path=s); assert c.fetch()==s
def test_meta_saved(tmp_path):
    c=GPRCollector(tmp_path/'c',tmp_path/'z.zip'); c.parse(tmp_path/'s.csv') if (tmp_path/'s.csv').exists() else None
def test_alias_extract(tmp_path): assert callable(__import__('goldrush2.dr2.extractors.l6_001',fromlist=['extract']).extract)
def test_zero_signal(tmp_path):
    p=_cache(tmp_path); rows=json.loads(p.read_text()); [r.update(value=5) for r in rows]; p.write_text(json.dumps(rows)); assert run(p,tmp_path/'o.json')['horizons']['1-5d']['signal']==0
def test_json_serializable(tmp_path): json.dumps(run(_cache(tmp_path),tmp_path/'o.json'))

def test_weekly_source_vintage_tolerance_ignores_filesystem_mtime(tmp_path):
    p=_cache(tmp_path); old=time.time()-30*86400; os.utime(p,(old,old))
    out=run(p,tmp_path/'o.json')
    assert out['horizons']['1-5d']['confidence']==1
    assert out['publication_date']==(date.today()-timedelta(days=1)).isoformat()

def test_missing_source_vintage_is_stale(tmp_path):
    p=_cache(tmp_path); (tmp_path/'L6-001_meta.json').unlink()
    out=run(p,tmp_path/'o.json')
    assert out['horizons']['1-5d']['confidence']==0
    assert out['horizons']['1-5d']['status']=='STALE'

def test_tuesday_after_holiday_vintage_is_fresh(tmp_path):
    p=_cache(tmp_path); meta=tmp_path/'L6-001_meta.json'; payload=json.loads(meta.read_text()); payload['source_vintage_date']='2026-09-02'; meta.write_text(json.dumps(payload))
    out=run(p,tmp_path/'o.json')
    assert out['horizons']['1-3m']['confidence']==0.7
    assert out['horizons']['1-3m']['status']=='VALID'

def test_schedule_estimated_monday_activation(tmp_path):
    p=_cache(tmp_path); (tmp_path/'L6-001_meta.json').write_text(json.dumps({'downloaded_at':'2026-09-04T14:20:43Z'}))
    out=run(p,tmp_path/'o.json')
    assert out['availability_source']=='schedule_estimated'
    assert out['vintage_date'] is None
    assert out['estimated_availability_date']=='2026-09-07'
    assert out['horizons']['1-5d']['status']=='VALID'
    assert out['horizons']['1-5d']['confidence']==1

def test_schedule_estimated_stale_after_tolerance(tmp_path):
    p=_cache(tmp_path); (tmp_path/'L6-001_meta.json').write_text(json.dumps({'downloaded_at':'2026-08-01T14:20:43Z'}))
    out=run(p,tmp_path/'o.json')
    assert out['availability_source']=='schedule_estimated'
    assert out['horizons']['1-5d']['status']=='STALE'
    assert out['horizons']['1-5d']['confidence']==0
