"""Shared OIS curve lookback helpers."""
from __future__ import annotations
from typing import Any
HORIZONS = ("1-5d", "1-3m", "1-3y", "3-10y")
LOOKBACKS = {"1-5d": 5, "1-3m": 63, "1-3y": 252, "3-10y": 756}
CONFIDENCE = {"1-5d": 1.0, "1-3m": 0.8, "1-3y": 0.6, "3-10y": 0.4}
def valid_series(rows: list[dict[str, Any]], tenor: str) -> list[dict[str, Any]]:
    result=[]
    for row in rows:
        point=next((p for p in row.get("curve",[]) if str(p.get("tenor","")).upper()==tenor),None)
        if point is not None and point.get("rate") is not None: result.append({"date":row["date"],"rate":float(point["rate"]),"source":row.get("source")})
    return sorted(result,key=lambda x:x["date"])
def change_horizon(series: list[dict[str, Any]], horizon: str, direction: int) -> dict[str, Any]:
    lookback=LOOKBACKS[horizon]
    if len(series)<=lookback: return {"signal":0,"confidence":0.0,"evidence":{"status":"INCOMPLETE","reason":"insufficient valid observations","required_observations":lookback+1,"available_observations":len(series)}}
    current, comparison=series[-1],series[-lookback-1]; change=round(current["rate"]-comparison["rate"],8); signal=1 if change*direction>0 else -1 if change*direction<0 else 0
    if current.get("source") != comparison.get("source"):
        return {"signal":0,"confidence":0.0,"evidence":{"status":"INCOMPLETE","reason":"source boundary prevents an unadjusted comparison","current_source":current.get("source"),"comparison_source":comparison.get("source"),"comparison_date":comparison["date"]}}
    return {"signal":signal,"confidence":CONFIDENCE[horizon],"evidence":{"current_rate":current["rate"],"comparison_rate":comparison["rate"],"comparison_date":comparison["date"],"change_pp":change,"current_source":current.get("source"),"comparison_source":comparison.get("source")}}
