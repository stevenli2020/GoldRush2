"""OFAC SDN delta collector."""
from __future__ import annotations
import json, re
from pathlib import Path
import requests
import xml.etree.ElementTree as ET
from .base import BaseCollector, SourceUnavailableError

class OFACCollector(BaseCollector):
    handles_vars=["L6-002"]
    ARCHIVE="https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/GetDeltaFileArchive"
    DOWNLOAD="https://sanctionslistservice.ofac.treas.gov/api/download/delta?filename="
    def __init__(self, cache_dir:Path, raw_path:Path, force=False, always_refresh=False, verbose=0, snapshot_path:Path|None=None):
        super().__init__(cache_dir,force,always_refresh,verbose); self.raw_path=Path(raw_path); self.snapshot_path=snapshot_path
    @property
    def cache_path(self): return self.cache_dir/"L6-002.json"
    @property
    def meta_path(self): return self.cache_dir/"L6-002_meta.json"
    @staticmethod
    def _local(tag): return tag.rsplit("}",1)[-1].lower()
    def _latest_file(self):
        year=__import__("datetime").date.today().year
        r=requests.get(self.ARCHIVE,params={"year":year},timeout=30); r.raise_for_status(); payload=r.json()
        items=payload if isinstance(payload,list) else payload.get("data",payload.get("items",[]))
        if not items: raise SourceUnavailableError("OFAC delta archive is empty")
        item=max(items,key=lambda x:x.get("publishDisplayDate",x.get("date","")))
        return item.get("fileName") or item.get("filename"), item.get("publishDisplayDate","")[:10]
    def fetch(self, force=False):
        try:
            name,pub=self._latest_file(); r=requests.get(self.DOWNLOAD+requests.utils.quote(name),timeout=30); r.raise_for_status(); self.raw_path.parent.mkdir(parents=True,exist_ok=True); self.raw_path.write_bytes(r.content); self._published=pub; return self.raw_path
        except Exception as exc:
            if self.snapshot_path and self.snapshot_path.exists(): return self.snapshot_path
            raise SourceUnavailableError(f"OFAC source unavailable: {exc}") from exc
    def parse(self, raw_path):
        root=ET.parse(raw_path).getroot(); events=[]; today=getattr(self,"_published",None) or __import__("datetime").date.today().isoformat()
        for elem in root.iter():
            action=elem.attrib.get("action") or elem.attrib.get("Action")
            if not action or action.upper() not in {"ADD","UPDATE","REMOVE"}: continue
            fields={self._local(c.tag):(" ".join((c.text or "").split())) for c in elem.iter() if c is not elem and c.text and len(list(c))==0}
            name=fields.get("firstName") or fields.get("lastName") or fields.get("name") or fields.get("uid") or "UNKNOWN"
            refs=[v for k,v in fields.items() if "ref" in k]
            events.append({"date":today,"action":action.upper(),"name":name,"entity_id":elem.attrib.get("uid") or fields.get("uid"),"type":fields.get("sdnType") or fields.get("type"),"description":" ".join(fields.values()),"references":refs})
        if not events: raise SourceUnavailableError("OFAC delta contains no ADD/UPDATE/REMOVE events")
        self._save_updated([],events,"full"); return self.cache_path
    def fetch_latest_observation_date(self):
        try: self.fetch(); return getattr(self,"_published",None) or __import__("datetime").date.today().isoformat()
        except Exception as exc: raise SourceUnavailableError(str(exc)) from exc
    def download_full(self): return json.loads(self.parse(self.fetch()).read_text())
