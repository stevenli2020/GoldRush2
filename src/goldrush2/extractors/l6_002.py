"""Deterministic OFAC event signal extraction."""
from __future__ import annotations
import json, os, tempfile
from pathlib import Path
CACHE_PATH=Path("data/cache/L6-002.json")
def _score(e):
    t=(e.get("description") or "").lower(); action=e.get("action","").upper(); s=40 if action=="ADD" and any(x in t for x in ("block","freeze")) else 20 if action=="ADD" and "designat" in t else 10 if action=="UPDATE" else 0
    if action == "REMOVE":
        return 0
    s+=30 if any(x in t for x in ("central bank","monetary authority","sovereign")) else 15 if "government" in t else 0
    s+=20 if any(x in t for x in ("property","assets","funds")) else 10
    s+=10 if "executive order" in t else 5 if "statute" in t else 0
    return min(100,s)
def run(cache_path=CACHE_PATH, output_path=Path("data/current/L6-002.json"), force_refresh=False, verbose=0):
    events=json.loads(Path(cache_path).read_text()) if Path(cache_path).exists() else []; active={}
    for e in events:
        key=e.get("entity_id") or e.get("name")
        if e.get("action")=="REMOVE": active.pop(key,None)
        else: active[key]={**e,"score":_score(e)}
    total=max((e["score"] for e in active.values()),default=0); top=next(iter(active.values()),None)
    short={"signal":1 if total>0 else 0,"confidence":total/100,"evidence":{"total_score":total,"active_events_count":len(active),"top_event":top.get("name") if top else None}}
    out={"variable_id":"L6-002","data_frequency":"Event-driven","source_name":"OFAC SDN Delta","source_url":"https://sanctionslists.ofac.treas.gov/","observation_date":max((e.get("date","") for e in events),default=None),"horizons":{"1-5d":short,"1-3m":{**short,"evidence":{"total_score":total}},"1-3y":{"signal":0,"confidence":0,"evidence":{"reason":"Event-driven signals are short-term; long-term disabled"}},"3-10y":{"signal":0,"confidence":0,"evidence":{"reason":"Event-driven signals are short-term; long-term disabled"}}}}
    output_path=Path(output_path); output_path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_path.parent, delete=False) as tmp:
        json.dump(out,tmp,indent=2); tmp.write("\n"); temporary=tmp.name
    os.replace(temporary, output_path)
    if verbose: print(f"[extract] L6-002 events={len(events)} active={len(active)} score={total}")
    return out
extract=run
