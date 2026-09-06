"""Deterministic GPRD_ACT signal extraction."""
from __future__ import annotations
import json, os
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
import pandas as pd
from goldrush2.paths import DR2_ROOT as PROJECT_ROOT
CACHE_PATH=PROJECT_ROOT / "data/cache/L6-001.json"
# V1 policy proposal: TRANCHE3_CONFIDENCE_DECAY_RULE_PROPOSAL.md.
# These are evidence-quality weights, not calibrated probabilities.
CONFIDENCE_BY_HORIZON = {"1-5d": 1.0, "1-3m": 0.7}
def run(cache_path=CACHE_PATH, output_path=PROJECT_ROOT / "data/current/L6-001.json", force_refresh=False, verbose=0):
    rows=json.loads(Path(cache_path).read_text()) if Path(cache_path).exists() else []
    df=pd.DataFrame(rows)
    if not df.empty: df["date"]=pd.to_datetime(df["date"]); df["value"]=pd.to_numeric(df["value"],errors="coerce"); df=df.dropna().sort_values("date")
    latest=df.iloc[-1] if len(df) else None; horizons={}
    meta_path=Path(cache_path).with_name("L6-001_meta.json")
    try: meta=json.loads(meta_path.read_text())
    except (OSError, ValueError): meta={}
    vintage=meta.get("source_vintage_date")
    vintage_date=date.fromisoformat(vintage) if isinstance(vintage,str) else None
    retrieved_at=meta.get("downloaded_at")
    estimated_availability_date=None
    availability_source="source_vintage" if vintage_date else None
    if vintage_date is None and isinstance(retrieved_at,str):
        try:
            retrieved_date=datetime.fromisoformat(retrieved_at.replace("Z","+00:00")).date()
            days_to_monday=(7-retrieved_date.weekday()) % 7
            estimated_availability_date=retrieved_date + timedelta(days=days_to_monday)
            availability_source="schedule_estimated"
        except ValueError:
            pass
    freshness_date=vintage_date or estimated_availability_date
    gap=(date.today()-freshness_date).days if freshness_date is not None else None
    for h,conf in CONFIDENCE_BY_HORIZON.items():
        if len(df)<60: horizons[h]={"signal":0,"confidence":0,"status":"INSUFFICIENT_DATA","evidence":{"reason":"Insufficient history for 60 observations"}}; continue
        vals=df["value"].tail(60); ma5=float(vals.tail(5).mean()); ma20=float(vals.tail(20).mean()); std=float(vals.std(ddof=0)); score=max(-1.0,min(1.0,(ma5-ma20)/max(std,0.1))); sig=1 if score>0 else -1 if score<0 else 0
        effective_conf=conf
        stale = freshness_date is None or gap is None or gap > 7
        if stale: sig, effective_conf = 0, 0
        horizons[h]={"signal":sig,"confidence":effective_conf,"status":"STALE" if stale else "VALID","evidence":{"data":{"score":score,"ma5":ma5,"ma20":ma20,"std60":std,"current_date":latest["date"].date().isoformat(),"publication_date":vintage if vintage_date else None,"vintage_date":vintage_date.isoformat() if vintage_date else None,"estimated_availability_date":estimated_availability_date.isoformat() if estimated_availability_date else None,"availability_source":availability_source}, **({"warning":"Source vintage/update evidence is missing or beyond the seven-day release tolerance; signal suppressed"} if stale else {})}}
    for h in ("1-3y","3-10y"): horizons[h]={"signal":0,"confidence":0,"status":"NOT_APPLICABLE","evidence":{"reason":"GPRD_ACT is a short-term indicator; long-term signals disabled"}}
    if latest is None: obs=None
    else: obs=latest["date"].date().isoformat()
    out={"variable_id":"L6-001","data_frequency":"Daily","source_name":"GPRD_ACT (Caldara–Iacoviello)","source_url":meta.get("source_url","https://www.matteoiacoviello.com/gpr.htm"),"observation_date":obs,"publication_date":vintage_date.isoformat() if vintage_date else None,"vintage_date":vintage_date.isoformat() if vintage_date else None,"retrieved_at":retrieved_at,"availability_source":availability_source,"estimated_availability_date":estimated_availability_date.isoformat() if estimated_availability_date else None,"horizons":horizons}
    output_path=Path(output_path); output_path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_path.parent, delete=False) as tmp:
        json.dump(out,tmp,indent=2); tmp.write("\n"); temporary=tmp.name
    os.replace(temporary, output_path)
    if verbose: print(f"[extract] L6-001 observations={len(df)} latest={obs}")
    return out
extract=run
