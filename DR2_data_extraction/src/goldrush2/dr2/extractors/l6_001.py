"""Deterministic GPRD_ACT signal extraction."""
from __future__ import annotations
import json, os
import tempfile
from datetime import date
from pathlib import Path
import pandas as pd
from goldrush2.paths import DR2_ROOT as PROJECT_ROOT
CACHE_PATH=PROJECT_ROOT / "data/cache/L6-001.json"
def run(cache_path=CACHE_PATH, output_path=PROJECT_ROOT / "data/current/L6-001.json", force_refresh=False, verbose=0):
    rows=json.loads(Path(cache_path).read_text()) if Path(cache_path).exists() else []
    df=pd.DataFrame(rows)
    if not df.empty: df["date"]=pd.to_datetime(df["date"]); df["value"]=pd.to_numeric(df["value"],errors="coerce"); df=df.dropna().sort_values("date")
    latest=df.iloc[-1] if len(df) else None; horizons={}
    gap=(date.today()-latest["date"].date()).days if latest is not None else None
    for h,conf in (("1-5d",1.0),("1-3m",0.7)):
        if len(df)<60: horizons[h]={"signal":0,"confidence":0,"evidence":{"reason":"Insufficient history for 60 observations"}}; continue
        vals=df["value"].tail(60); ma5=float(vals.tail(5).mean()); ma20=float(vals.tail(20).mean()); std=float(vals.std(ddof=0)); score=max(-1.0,min(1.0,(ma5-ma20)/max(std,0.1))); sig=1 if score>0 else -1 if score<0 else 0
        effective_conf=conf
        if gap is not None and gap > 3: sig, effective_conf = 0, 0
        elif gap is not None and gap > 1: effective_conf = 0
        horizons[h]={"signal":sig,"confidence":effective_conf,"evidence":{"data":{"score":score,"ma5":ma5,"ma20":ma20,"std60":std,"current_date":latest["date"].date().isoformat()}, **({"warning":"Cached data is stale; last computed signal retained with zero confidence"} if gap is not None and 1 < gap <= 3 else {"warning":"Cached data is stale; signal suppressed"} if gap is not None and gap > 3 else {})}}
    for h in ("1-3y","3-10y"): horizons[h]={"signal":0,"confidence":0,"evidence":{"reason":"GPRD_ACT is a short-term indicator; long-term signals disabled"}}
    if latest is None: obs=None
    else: obs=latest["date"].date().isoformat()
    out={"variable_id":"L6-001","data_frequency":"Daily","source_name":"GPRD_ACT (Caldara–Iacoviello)","source_url":"https://www.matteoiacoviello.com/gpr.htm","observation_date":obs,"horizons":horizons}
    output_path=Path(output_path); output_path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_path.parent, delete=False) as tmp:
        json.dump(out,tmp,indent=2); tmp.write("\n"); temporary=tmp.name
    os.replace(temporary, output_path)
    if verbose: print(f"[extract] L6-001 observations={len(df)} latest={obs}")
    return out
extract=run
