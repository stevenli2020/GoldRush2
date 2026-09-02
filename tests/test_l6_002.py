import json
from goldrush2.collectors.ofac import OFACCollector
from goldrush2.extractors.l6_002 import run, _score
def test_parse_events(tmp_path):
    x=tmp_path/'x.xml'; x.write_text('<sdnList><sdnEntry action="ADD" uid="1"><firstName>Bank</firstName><remarks>block property central bank Executive Order</remarks></sdnEntry></sdnList>'); c=OFACCollector(tmp_path/'c',tmp_path/'r.xml'); c.parse(x); assert json.loads(c.cache_path.read_text())[0]['action']=='ADD'
def test_score_block(): assert _score({'action':'ADD','description':'block property central bank Executive Order'})==100
def test_score_update(): assert _score({'action':'UPDATE','description':'government funds'})>0
def test_score_remove(): assert _score({'action':'REMOVE','description':'anything'})==0
def test_active_signal(tmp_path):
    p=tmp_path/'c.json'; p.write_text(json.dumps([{'date':'2026-01-01','action':'ADD','name':'x','description':'block property'}])); assert run(p,tmp_path/'o.json')['horizons']['1-5d']['signal']==1
def test_no_events(tmp_path):
    p=tmp_path/'c.json'; p.write_text('[]'); assert run(p,tmp_path/'o.json')['horizons']['1-5d']['signal']==0
def test_remove(tmp_path):
    p=tmp_path/'c.json'; p.write_text(json.dumps([{'date':'2026-01-01','action':'ADD','name':'x','description':'block'}, {'date':'2026-01-02','action':'REMOVE','name':'x'}])); assert run(p,tmp_path/'o.json')['horizons']['1-5d']['signal']==0
def test_long_disabled(tmp_path):
    p=tmp_path/'c.json'; p.write_text('[]'); assert run(p,tmp_path/'o.json')['horizons']['3-10y']['confidence']==0
def test_confidence_ratio(tmp_path):
    p=tmp_path/'c.json'; p.write_text(json.dumps([{'date':'2026-01-01','action':'ADD','name':'x','description':'government'}])); assert run(p,tmp_path/'o.json')['horizons']['1-5d']['confidence']==.25
def test_output_file(tmp_path):
    p=tmp_path/'c.json'; p.write_text('[]'); run(p,tmp_path/'o.json'); assert (tmp_path/'o.json').exists()
def test_snapshot(tmp_path, monkeypatch):
    s=tmp_path/'s.xml'; s.write_text('<x/>')
    monkeypatch.setattr('goldrush2.collectors.ofac.requests.post', lambda *a, **k: (_ for _ in ()).throw(RuntimeError('offline')))
    monkeypatch.setattr('goldrush2.collectors.ofac.requests.head', lambda *a, **k: (_ for _ in ()).throw(RuntimeError('offline')))
    c=OFACCollector(tmp_path/'c',tmp_path/'r.xml',snapshot_path=s); assert c.fetch()==s
def test_fields(tmp_path):
    p=tmp_path/'c.json'; p.write_text('[]'); assert run(p,tmp_path/'o.json')['variable_id']=='L6-002'
def test_event_count(tmp_path):
    p=tmp_path/'c.json'; p.write_text(json.dumps([{'date':'2026','action':'ADD','name':'x','description':'funds'}])); assert run(p,tmp_path/'o.json')['horizons']['1-5d']['evidence']['active_events_count']==1
def test_json(tmp_path):
    p=tmp_path/'c.json'; p.write_text('[]'); json.dumps(run(p,tmp_path/'o.json'))
def test_source(tmp_path):
    p=tmp_path/'c.json'; p.write_text('[]'); assert 'ofac' in run(p,tmp_path/'o.json')['source_url']
