"""Data models for GR2 analytics (DR3)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class SourceInfo:
    name: str
    url: str
    observation_date: str

@dataclass
class EvidenceData:
    latest_value: Optional[float] = None
    comparison_value: Optional[float] = None
    change: Optional[float] = None
    unit: Optional[str] = None
    applicable: Optional[bool] = None
    @classmethod
    def from_dict(cls, data: dict) -> "EvidenceData":
        return cls(**{k: data.get(k) for k in cls.__dataclass_fields__})

@dataclass
class Evidence:
    data: EvidenceData
    summary: str
    @classmethod
    def from_dict(cls, data: dict) -> "Evidence":
        return cls(data=EvidenceData.from_dict(data.get("data", {})), summary=data.get("summary", ""))

@dataclass
class HorizonSignal:
    signal: int
    confidence: float
    evidence: Evidence
    @classmethod
    def from_dict(cls, data: dict) -> "HorizonSignal":
        return cls(signal=data.get("signal", 0), confidence=data.get("confidence", 0.0), evidence=Evidence.from_dict(data.get("evidence", {})))

@dataclass
class VariableResult:
    variable_id: str
    as_of_date: str
    sources: list[SourceInfo]
    horizons: dict[str, HorizonSignal]
    @classmethod
    def from_dict(cls, data: dict) -> "VariableResult":
        sources = [SourceInfo(**{k: s.get(k) for k in SourceInfo.__dataclass_fields__}) for s in data.get("sources", [])]
        horizons = {k: HorizonSignal.from_dict(v) for k, v in data.get("horizons", {}).items()}
        return cls(variable_id=data.get("variable_id", ""), as_of_date=data.get("as_of_date", ""), sources=sources, horizons=horizons)

@dataclass
class HorizonScore:
    horizon: str
    score: int
    raw_score: float
    confidence: float
    data_availability: float
    status: str
    contributing_variables: int
    total_configured_variables: int
    top_bullish: list[str] = field(default_factory=list)
    top_bearish: list[str] = field(default_factory=list)
    low_confidence_contributors: list[dict] = field(default_factory=list)
    def to_dict(self) -> dict:
        return {"horizon": self.horizon, "score": self.score, "raw_score": round(self.raw_score, 6), "confidence": round(self.confidence, 4), "data_availability": round(self.data_availability, 4), "status": self.status, "contributing_variables": self.contributing_variables, "total_configured_variables": self.total_configured_variables, "top_bullish": self.top_bullish, "top_bearish": self.top_bearish, "low_confidence_contributors": self.low_confidence_contributors}

@dataclass
class AggregatedResult:
    generated_at: str
    weight_schema_version: str
    horizons: dict[str, HorizonScore]
    warnings: list[str] = field(default_factory=list)
    def to_dict(self) -> dict:
        return {"generated_at": self.generated_at, "weight_schema_version": self.weight_schema_version, "horizons": {k: v.to_dict() for k, v in self.horizons.items()}, "warnings": self.warnings}
