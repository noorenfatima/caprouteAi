"""ML decision wrapper for CapRoute AI.

This module wraps the existing FrictionScorer without changing its prediction
behavior. It also centralizes the legacy rule-based fallback used by logic.py.
"""

import os
from typing import Any, Dict, Optional

from backend.features import build_features_from_zone
from backend.models import MLDecision


class MLDecisionEngine:
    def __init__(self, model_path: str = "friction_model.pkl"):
        self.model_path = model_path
        self.scorer = None
        self.load_error: Optional[str] = None

        if os.path.exists(model_path):
            try:
                from ml_model import FrictionScorer

                self.scorer = FrictionScorer(model_path)
                print("[ML] Loaded FrictionScorer model successfully.")
            except Exception as exc:
                self.load_error = str(exc)
                print(f"[ML] Error loading FrictionScorer: {exc}")

    @property
    def is_available(self) -> bool:
        return self.scorer is not None

    def predict_compliance(
        self,
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
        zone_logic: Dict[str, Any],
    ) -> MLDecision:
        if self.scorer:
            try:
                features = build_features_from_zone(
                    zone_logic=zone_logic,
                    withholding_tax_rate=withholding_tax_rate,
                    landing_fee_avg=landing_fee_avg,
                    fx_spread=fx_spread,
                    purpose=purpose,
                    amount_usd=amount_usd,
                    zone_name=zone_name,
                    business_size=business_size,
                )
                compliance_score, feature_importances = self.scorer.predict(
                    withholding_tax_rate=features.withholding_tax_rate,
                    additional_local_tax=features.additional_local_tax,
                    correspondent_hops=features.correspondent_hops,
                    compliance_latency_hrs=features.compliance_latency_hrs,
                    landing_fee_avg=features.landing_fee_avg,
                    fx_spread=features.fx_spread,
                    purpose=purpose,
                    amount_usd=amount_usd,
                    zone_name=zone_name,
                    is_mandatory_validation=bool(features.is_mandatory_validation),
                    business_size=business_size,
                )
                return MLDecision(
                    compliance_score=compliance_score,
                    feature_importances=feature_importances,
                    model_used="friction_model.pkl",
                )
            except Exception as exc:
                print(f"[ML] Inference failed: {exc}. Falling back to rule-based compliance score.")
                return MLDecision(
                    compliance_score=self.rule_based_compliance_score(zone_logic),
                    feature_importances={},
                    model_used="rule_based_fallback",
                    fallback_reason=str(exc),
                )

        return MLDecision(
            compliance_score=self.rule_based_compliance_score(zone_logic),
            feature_importances={},
            model_used="rule_based_fallback",
            fallback_reason=self.load_error or "model_unavailable",
        )

    @staticmethod
    def rule_based_compliance_score(zone_logic: Dict[str, Any]) -> float:
        compliance_score = 100
        compliance_score -= zone_logic.get("avg_correspondent_hops", 1) * 5
        if zone_logic.get("additional_local_tax_pct", 0) > 0:
            compliance_score -= 15
        if zone_logic.get("mandatory_purpose_code_validation", False):
            compliance_score += 10
        return max(0, min(100, compliance_score))
