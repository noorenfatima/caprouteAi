"""Shared domain models for the CapRoute AI backend.

These models mirror the existing runtime concepts without changing the public
FastAPI contracts. Current compatibility wrappers can keep using legacy import
paths while new modules depend on this file.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class Purpose(Enum):
    EXPORT = "EXPORT"
    SERVICE = "SERVICE"
    INVESTMENT = "INVESTMENT"
    SALARY = "SALARY"
    ROYALTY = "ROYALTY"


class BusinessSize(Enum):
    SMALL = "SMALL"
    LARGE = "LARGE"


class Priority(Enum):
    COST = "COST"
    TIME = "TIME"
    BALANCED = "BALANCED"


class CurrencyHandling(Enum):
    CONVERT = "CONVERT"
    HOLD = "HOLD"


@dataclass
class Route:
    path: List[str]
    total_cost_usd: float
    total_time_hrs: float
    compliance_score: float
    breakdown: Dict[str, Any]

    def __repr__(self) -> str:
        path_display = " -> ".join(self.path)
        return (
            f"Route(path={path_display}, cost=${self.total_cost_usd:.2f}, "
            f"time={self.total_time_hrs:.1f}h, compliance={self.compliance_score:.1f}/100)"
        )


@dataclass(frozen=True)
class CorridorHop:
    source: str
    destination: str
    zone_name: str
    zone_logic: Dict[str, Any]


@dataclass(frozen=True)
class CorridorCandidate:
    path: List[str]
    hops: List[CorridorHop]


@dataclass(frozen=True)
class FeatureVector:
    withholding_tax_rate: float
    additional_local_tax: float
    correspondent_hops: int
    compliance_latency_hrs: float
    landing_fee_avg: float
    fx_spread: float
    purpose_risk: float
    amount_log: float
    zone_risk: float
    is_mandatory_validation: int
    business_size: int

    def as_list(self) -> List[float]:
        return [
            self.withholding_tax_rate,
            self.additional_local_tax,
            float(self.correspondent_hops),
            self.compliance_latency_hrs,
            self.landing_fee_avg,
            self.fx_spread,
            self.purpose_risk,
            self.amount_log,
            self.zone_risk,
            float(self.is_mandatory_validation),
            float(self.business_size),
        ]


@dataclass(frozen=True)
class MLDecision:
    compliance_score: float
    feature_importances: Dict[str, float]
    model_used: str
    fallback_reason: Optional[str] = None

