"""Caldara-Iacoviello daily geopolitical risk collector."""
from __future__ import annotations
import io, json, tempfile, zipfile, re
from urllib.parse import urljoin
from pathlib import Path
from typing import Any
import pandas as pd
import requests
from .base import BaseCollector, SourceUnavailableError

class GPRCollector(BaseCollector):
    handles_vars = ["L6-001"]
    SOURCE_URL = "https://www.matteoiacoviello.com/gpr.htm"
    def __init__(self, cache_dir: Path, raw_path: Path, force=False, always_refresh=False, verbose=0, snapshot_path: Path|None=None):
        super().__init__(cache_dir, force, always_refresh, verbose); self.raw_path=Path(raw_path); self.snapshot_path=snapshot_path
    @property
    def cache_path(self): return self.cache_dir / "L6-001.json"
    @property
    def meta_path(self): return self.cache_dir / "L6-001_meta.json"
    def fetch(self, force=False):
        if self.raw_path.exists() and not (force or self.force): return self.raw_path
        try:
            page=requests.get(self.SOURCE_URL, timeout=30); page.raise_for_status()
            match=re.search(r'href=["\']([^"\']*data_gpr_daily_recent(?:_[0-9]{8})?\.dta)["\']', page.text, re.I)
            if not match: raise SourceUnavailableError("GPR page contains no daily DTA link")
            url=urljoin(self.SOURCE_URL, match.group(1)); r=requests.get(url, timeout=30); r.raise_for_status(); self.raw_path.parent.mkdir(parents=True, exist_ok=True); self.raw_path.write_bytes(r.content); self.source_url=url; return self.raw_path
        except Exception as exc:
            if self.snapshot_path and self.snapshot_path.exists(): return self.snapshot_path
            raise SourceUnavailableError(f"GPR source unavailable: {exc}") from exc
    def _read(self, path):
        if path.suffix.lower()==".csv": return pd.read_csv(path)
        try:
            with zipfile.ZipFile(path) as z:
                name=next((n for n in z.namelist() if n.lower().endswith(".dta")), None)
                if not name: raise SourceUnavailableError("GPR archive contains no DTA file")
                return pd.read_stata(io.BytesIO(z.read(name)))
        except zipfile.BadZipFile:
            # The raw path retains the historical .zip name; pass bytes so
            # pandas does not infer ZIP compression from that suffix.
            return pd.read_stata(io.BytesIO(path.read_bytes()))
    def parse(self, raw_path):
        df=self._read(Path(raw_path)); cols={str(c).lower():c for c in df.columns}
        if "date" not in cols or "gprd_act" not in cols: raise SourceUnavailableError("GPR data lacks date/GPRD_ACT columns")
        out=[]
        for _, row in df.iterrows():
            try:
                val=float(row[cols["gprd_act"]]); dt=pd.to_datetime(row[cols["date"]], errors="coerce")
                if pd.isna(dt) or not pd.notna(val): continue
                out.append({"date":dt.date().isoformat(),"value":val})
            except (TypeError,ValueError): continue
        if not out: raise SourceUnavailableError("GPR data contains no valid observations")
        self._save_updated([], out, "full"); return self.cache_path
    def fetch_latest_observation_date(self):
        try:
            p=self.fetch(); df=self._read(Path(p)); dt=pd.to_datetime(df[ next(c for c in df.columns if str(c).lower()=="date") ], errors="coerce").max(); return dt.date().isoformat()
        except Exception as exc: raise SourceUnavailableError(str(exc)) from exc
    def download_full(self):
        p=self.fetch(); return json.loads(self.parse(p).read_text())
