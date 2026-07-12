"""Feature engineering for CapRoute AI corridor friction scoring.

The trained model expects these 11 features in this exact order. This module is
the canonical Phase 1 home for that ordering and the domain mappings.
"""

import math
from typing import Any, Dict

import numpy as np

from backend.models import FeatureVector


PURPOSE_RISK = {
    "EXPORT": 0.1,
    "SERVICE": 0.2,
    "SALARY": 0.15,
    "ROYALTY": 0.35,
    "INVESTMENT": 0.45,
    "FDI_INVESTMENT": 0.55,
    "STOCK_MARKET": 0.50,
}

BUSINESS_SIZE_MAP = {"SMALL": 0, "LARGE": 1}

ZONE_RISK = {
    "ZONE_A_DTAA_PRIME": 0.10,
    "ZONE_B_TAX_HAVEN_LOW_FRICTION": 0.30,
    "ZONE_C_HIGH_COMPLIANCE": 0.65,
    "ORIGIN": 0.0,
}

FEATURE_NAMES = [
    "withholding_tax_rate",
    "additional_local_tax",
    "correspondent_hops",
    "compliance_latency_hrs",
    "landing_fee_avg",
    "fx_spread",
    "purpose_risk",
    "amount_log",
    "zone_risk",
    "is_mandatory_validation",
    "business_size",
]


def build_feature_vector(
    withholding_tax_rate: float,
    additional_local_tax: float,
    correspondent_hops: int,
    compliance_latency_hrs: float,
    landing_fee_avg: float,
    fx_spread: float,
    purpose_risk: float,
    amount_log: float,
    zone_risk: float,
    is_mandatory_validation: int,
    business_size: int,
) -> np.ndarray:
    """Return the model-ready 1-D feature vector in trained order."""
    return np.array(
        [
            withholding_tax_rate,
            additional_local_tax,
            float(correspondent_hops),
            compliance_latency_hrs,
            landing_fee_avg,
            fx_spread,
            purpose_risk,
            amount_log,
            zone_risk,
            float(is_mandatory_validation),
            float(business_size),
        ],
        dtype=np.float32,
    )


def feature_vector_to_array(feature: FeatureVector) -> np.ndarray:
    """Convert an interpretable FeatureVector into model-ready numpy shape."""
    return build_feature_vector(
        withholding_tax_rate=feature.withholding_tax_rate,
        additional_local_tax=feature.additional_local_tax,
        correspondent_hops=feature.correspondent_hops,
        compliance_latency_hrs=feature.compliance_latency_hrs,
        landing_fee_avg=feature.landing_fee_avg,
        fx_spread=feature.fx_spread,
        purpose_risk=feature.purpose_risk,
        amount_log=feature.amount_log,
        zone_risk=feature.zone_risk,
        is_mandatory_validation=feature.is_mandatory_validation,
        business_size=feature.business_size,
    )


def build_corridor_features(
    *,
    withholding_tax_rate: float,
    additional_local_tax: float,
    correspondent_hops: int,
    compliance_latency_hrs: float,
    landing_fee_avg: float,
    fx_spread: float,
    purpose: str,
    amount_usd: float,
    zone_name: str,
    is_mandatory_validation: bool,
    business_size: str,
) -> FeatureVector:
    """Build an interpretable feature object before conversion to model input."""
    return FeatureVector(
        withholding_tax_rate=withholding_tax_rate,
        additional_local_tax=additional_local_tax,
        correspondent_hops=correspondent_hops,
        compliance_latency_hrs=compliance_latency_hrs,
        landing_fee_avg=landing_fee_avg,
        fx_spread=fx_spread,
        purpose_risk=PURPOSE_RISK.get(purpose.upper(), 0.2),
        amount_log=math.log10(max(amount_usd, 1)),
        zone_risk=ZONE_RISK.get(zone_name, 0.3),
        is_mandatory_validation=int(is_mandatory_validation),
        business_size=BUSINESS_SIZE_MAP.get(business_size.upper(), 0),
    )


def build_features_from_zone(
    *,
    zone_logic: Dict[str, Any],
    withholding_tax_rate: float,
    landing_fee_avg: float,
    fx_spread: float,
    purpose: str,
    amount_usd: float,
    zone_name: str,
    business_size: str,
) -> FeatureVector:
    """Build the 11 financial features from existing zone/config values."""
    return build_corridor_features(
        withholding_tax_rate=withholding_tax_rate,
        additional_local_tax=zone_logic.get("additional_local_tax_pct", 0.0),
        correspondent_hops=zone_logic.get("avg_correspondent_hops", 1),
        compliance_latency_hrs=zone_logic.get("compliance_latency_hrs", 24),
        landing_fee_avg=landing_fee_avg,
        fx_spread=fx_spread,
        purpose=purpose,
        amount_usd=amount_usd,
        zone_name=zone_name,
        is_mandatory_validation=zone_logic.get("mandatory_purpose_code_validation", False),
        business_size=business_size,
    )
