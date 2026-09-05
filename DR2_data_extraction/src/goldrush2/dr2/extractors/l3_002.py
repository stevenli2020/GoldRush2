"""L3-002: directional change in the 1Y USD SOFR OIS rate."""
from __future__ import annotations
import json, os
from pathlib import Path
from typing import Any
from goldrush2.dr2.extractors._ois_common import HORIZONS, change_horizon, valid_series
from goldrush2.paths import DR2_ROOT
VARIABLE_ID="L3-002"; SOURCE_NAME="USD SOFR OIS Curve - 1Y policy path"; SOURCE_URL="http://188.166.178.188/temp/datafeed/"
CACHE_PATH=DR2_ROOT/"data"/"cache"/"ois"/"ois_curves.json"; OUTPUT_PATH=DR2_ROOT/"data"/"current"/"L3-002.json"
def build_output(rows: list[dict[str, Any]]) -> dict[str, Any]:
    series=valid_series(rows,"1Y")
    return {"variable_id":VARIABLE_ID,"data_frequency":"Daily","source_name":SOURCE_NAME,"source_url":SOURCE_URL,"observation_date":series[-1]["date"] if series else None,"metric":"1Y OIS rate","horizons":{h:change_horizon(series,h,-1) for h in HORIZONS}}
def run(*, output_path: Path=OUTPUT_PATH, cache_path: Path=CACHE_PATH) -> dict[str, Any]:
    output=build_output(json.loads(cache_path.read_text(encoding="utf-8"))); output_path.parent.mkdir(parents=True,exist_ok=True); temporary=output_path.with_suffix(".tmp"); temporary.write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8"); os.replace(temporary,output_path); return output
