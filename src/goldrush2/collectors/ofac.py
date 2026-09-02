"""OFAC SDN delta collector."""
from __future__ import annotations
import json, re
from datetime import date, timedelta
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
    @property
    def state_path(self): return self.cache_dir/"L6-002_state.json"
    @staticmethod
    def _local(tag): return tag.rsplit("}",1)[-1].lower()
    @staticmethod
    def _event_score(event):
        text=(event.get("description") or "").lower(); action=event.get("action","")
        if action=="REMOVE": return 0
        score=40 if action=="ADD" and any(w in text for w in ("block","freeze")) else 20 if action=="ADD" and "designat" in text else 10 if action=="UPDATE" else 0
        score += 30 if any(w in text for w in ("central bank","monetary authority","sovereign")) else 15 if "government" in text else 0
        score += 20 if any(w in text for w in ("property","assets","funds")) else 10
        score += 10 if "executive order" in text else 5 if "statute" in text else 0
        return min(score,100)
    def _latest_file(self):
        # Prefer the documented date-based delta URLs, then use OFAC's archive API.
        # Delta publication can be delayed by weekends and holidays; search a
        # full 30-day window before falling back to the complete SDN baseline.
        for days in range(30):
            d=date.today()-timedelta(days=days)
            for stamp in (d.strftime("%Y-%m-%d"), d.strftime("%m%d%Y"), d.strftime("%Y%m%d")):
                url=f"https://sanctionslists.ofac.treas.gov/deltas/sdn_delta_{stamp}.xml"
                try:
                    h=requests.head(url,timeout=10,allow_redirects=True)
                    if h.status_code==200: return url, d.isoformat()
                except requests.RequestException: pass
        r=requests.get(self.ARCHIVE,params={"year":date.today().year},timeout=30); r.raise_for_status(); payload=r.json()
        items=payload if isinstance(payload,list) else payload.get("data",payload.get("items",[]))
        if not items: return "https://sanctionslists.ofac.treas.gov/sdn.xml", date.today().isoformat()
        item=max(items,key=lambda x:x.get("publishDisplayDate",x.get("date","")))
        name=item.get("fileName") or item.get("filename")
        return self.DOWNLOAD+requests.utils.quote(name), item.get("publishDisplayDate","")[:10]
    def fetch(self, force=False):
        try:
            url,pub=self._latest_file(); r=requests.get(url,timeout=30); r.raise_for_status(); self.raw_path.parent.mkdir(parents=True,exist_ok=True); self.raw_path.write_bytes(r.content); self._published=pub; return self.raw_path
        except Exception as exc:
            if self.snapshot_path and self.snapshot_path.exists(): return self.snapshot_path
            raise SourceUnavailableError(f"OFAC source unavailable: {exc}") from exc
    def parse(self, raw_path):
        root=ET.parse(raw_path).getroot(); events=[]; today=getattr(self,"_published",None) or __import__("datetime").date.today().isoformat()
        for elem in root.iter():
            tag=self._local(elem.tag); action=elem.attrib.get("action") or elem.attrib.get("Action")
            if not action and tag in {"add","update","remove"}: action=tag.upper()
            if not action or action.upper() not in {"ADD","UPDATE","REMOVE"}: continue
            fields={self._local(c.tag):(" ".join((c.text or "").split())) for c in elem.iter() if c is not elem and c.text and len(list(c))==0}
            name=fields.get("firstName") or fields.get("lastName") or fields.get("name") or fields.get("uid") or "UNKNOWN"
            refs=[v for k,v in fields.items() if "ref" in k]
            events.append({"date":today,"action":action.upper(),"name":name,"entity_id":elem.attrib.get("uid") or fields.get("uid"),"type":fields.get("sdnType") or fields.get("type"),"description":" ".join(fields.values()),"references":refs})
        if not events and any(self._local(e.tag)=="sdnentry" for e in root.iter()):
            for elem in root.iter():
                if self._local(elem.tag)!="sdnentry": continue
                fields={self._local(c.tag):(" ".join((c.text or "").split())) for c in elem.iter() if c is not elem and c.text and len(list(c))==0}
                events.append({"date":today,"action":"ADD","name":fields.get("firstName") or fields.get("lastName") or "UNKNOWN","entity_id":elem.attrib.get("uid"),"type":fields.get("sdnType"),"description":" ".join(fields.values()),"references":[]})
        if not events: raise SourceUnavailableError("OFAC delta contains no ADD/UPDATE/REMOVE events")
        existing=self.load_cache(); rows=self._save_updated(existing,events,"full")
        active={}
        for e in rows:
            key=e.get("entity_id") or e.get("name")
            if e.get("action")=="REMOVE": active.pop(key,None)
            else: active[key]={**e,"score":self._event_score(e)}
        self._atomic_json(self.state_path,{"active_events":list(active.values()),"last_processed_date":today})
        return self.cache_path
    def fetch_latest_observation_date(self):
        try: self.fetch(); return getattr(self,"_published",None) or __import__("datetime").date.today().isoformat()
        except Exception as exc: raise SourceUnavailableError(str(exc)) from exc
    def download_full(self): return json.loads(self.parse(self.fetch()).read_text())
