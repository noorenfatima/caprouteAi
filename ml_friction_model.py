"""
ML Friction Scoring Engine for CapRoute AI
==========================================
Trains a Random Forest + XGBoost ensemble on synthetic corridor data
derived from capital_routing_config.json.

Replaces the hardcoded compliance_score formula in logic.py with a
real ML prediction. Features are interpretable and explainable to faculty.

Output: friction_model.pkl  (loaded at server startup)
"""

import json
import math
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from typing import Dict, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# 1. FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────

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
    "ZONE_B_TAX_HAVEN_LOW_FRICTION": 0.30,   # Low cost but regulatory scrutiny
    "ZONE_C_HIGH_COMPLIANCE": 0.65,
    "ORIGIN": 0.0,
}

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
    """Returns a 1-D feature vector for model input."""
    return np.array([
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
    ], dtype=np.float32)

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

# ─────────────────────────────────────────────────────────────────────────────
# 2. SYNTHETIC TRAINING DATA GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_training_data(config_path: str = "capital_routing_config.json", n_samples: int = 8000) -> pd.DataFrame:
    """
    Generates synthetic labelled training samples from the routing config.
    
    Label (friction_score 0–100):
      0   = zero friction (same-currency, DTAA prime, no hops)
      100 = maximum friction (Zone C, high compliance latency, heavy taxes)
    
    Domain-expert formula encodes what "friction" means in cross-border finance,
    then we add calibrated noise so the model must *learn* not just memorise.
    """
    with open(config_path) as f:
        config = json.load(f)

    rng = np.random.default_rng(42)
    rows = []

    origins = config["base_origins"]
    amounts = np.logspace(3, 7, 50)       # $1k – $10M range

    for origin_name, origin_data in origins.items():
        asset_coefs = origin_data.get("asset_specific_coefficients", {})
        normal = asset_coefs.get("NORMAL_TRANSFER", {})
        fx_spread_base = (normal.get("fx_spread_bank", 0.035) + normal.get("fx_spread_fintech", 0.006)) / 2

        dest_zones = origin_data.get("destination_zones", {})
        for zone_name, zone_data in dest_zones.items():
            logic = zone_data.get("logic", {})
            zone_risk_val = ZONE_RISK.get(zone_name, 0.3)

            for purpose, p_risk in PURPOSE_RISK.items():
                for biz_size_str, biz_size_int in BUSINESS_SIZE_MAP.items():
                    for amount in amounts:
                        # Core corridor features
                        wht = logic.get("withholding_tax_dividends", 0.0) if "INVEST" in purpose or "STOCK" in purpose \
                              else logic.get("withholding_tax_interest", 0.0)
                        add_tax = logic.get("additional_local_tax_pct", 0.0)
                        hops = logic.get("avg_correspondent_hops", 1)
                        latency = logic.get("compliance_latency_hrs", 24)
                        fee_range = logic.get("landing_fee_range_usd", [10, 30])
                        landing_avg = (fee_range[0] + fee_range[1]) / 2
                        mandatory = int(logic.get("mandatory_purpose_code_validation", False))

                        # FX spread depends on business size
                        fx_spread = normal.get("fx_spread_fintech", 0.006) if biz_size_int == 1 \
                                    else normal.get("fx_spread_bank", 0.035)
                        amount_log = math.log10(max(amount, 1))

                        # ── DOMAIN EXPERT LABEL ──────────────────────────────
                        # Each component contributes to friction on [0,1] scale
                        tax_friction      = min(wht * 2, 1.0)                    # 0–50% wht → 0–1
                        hop_friction      = min(hops / 3.0, 1.0)                 # 0–3 hops → 0–1
                        latency_friction  = min(latency / 72.0, 1.0)             # 0–72h → 0–1
                        fee_friction      = min(landing_avg / 75.0, 1.0)         # $0–75 → 0–1
                        add_tax_friction  = min(add_tax * 20, 1.0)               # 0–5% → 0–1
                        fx_friction       = min(fx_spread * 15, 1.0)             # 0–4% → 0–1
                        purpose_friction  = p_risk
                        zone_friction     = zone_risk_val
                        mandatory_penalty = 0.1 * mandatory

                        # Weighted sum (weights reflect real-world priority)
                        raw = (
                            0.20 * tax_friction +
                            0.15 * hop_friction +
                            0.15 * latency_friction +
                            0.10 * fee_friction +
                            0.10 * add_tax_friction +
                            0.10 * fx_friction +
                            0.10 * purpose_friction +
                            0.05 * zone_friction +
                            0.05 * mandatory_penalty
                        )
                        label = min(max(raw * 100, 0), 100)

                        # Add realistic noise (±5 pts std)
                        noise = rng.normal(0, 5)
                        label_noisy = float(np.clip(label + noise, 0, 100))

                        rows.append({
                            "withholding_tax_rate": wht,
                            "additional_local_tax": add_tax,
                            "correspondent_hops": hops,
                            "compliance_latency_hrs": latency,
                            "landing_fee_avg": landing_avg,
                            "fx_spread": fx_spread,
                            "purpose_risk": p_risk,
                            "amount_log": amount_log,
                            "zone_risk": zone_risk_val,
                            "is_mandatory_validation": mandatory,
                            "business_size": biz_size_int,
                            "friction_score": label_noisy,
                            # metadata (not used as features)
                            "_origin": origin_name,
                            "_zone": zone_name,
                            "_purpose": purpose,
                        })

    df = pd.DataFrame(rows)

    # Upsample with augmented perturbations to reach n_samples
    if len(df) < n_samples:
        extras = df.sample(n=n_samples - len(df), replace=True, random_state=99)
        for col in FEATURE_NAMES[:-1]:   # add small jitter to numeric features
            extras[col] = extras[col] + rng.normal(0, 0.005, len(extras))
        extras["friction_score"] = np.clip(extras["friction_score"] + rng.normal(0, 3, len(extras)), 0, 100)
        df = pd.concat([df, extras], ignore_index=True)

    return df.sample(frac=1, random_state=42).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# 3. MODEL TRAINING
# ─────────────────────────────────────────────────────────────────────────────

def train_model(config_path: str = "capital_routing_config.json") -> Dict:
    """
    Trains an ensemble of Random Forest + Gradient Boosting regressors.
    Returns a dict with model, feature importances, and eval metrics.
    """
    print("🔬 Generating synthetic training data...")
    df = generate_training_data(config_path)
    print(f"   ✅ {len(df)} samples generated across {df['_origin'].nunique()} origins × {df['_zone'].nunique()} zones × {df['_purpose'].nunique()} purposes")

    X = df[FEATURE_NAMES].values
    y = df["friction_score"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # ── Random Forest ─────────────────────────────────────────────────────────
    print("\n🌲 Training Random Forest...")
    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=4,
        max_features=0.7,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    rf_mae = mean_absolute_error(y_test, rf_preds)
    rf_r2 = r2_score(y_test, rf_preds)
    print(f"   RF  → MAE: {rf_mae:.3f} pts | R²: {rf_r2:.4f}")

    # ── Gradient Boosting ─────────────────────────────────────────────────────
    print("\n🚀 Training Gradient Boosting (XGBoost-style)...")
    gb = GradientBoostingRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        min_samples_leaf=5,
        random_state=42,
    )
    gb.fit(X_train, y_train)
    gb_preds = gb.predict(X_test)
    gb_mae = mean_absolute_error(y_test, gb_preds)
    gb_r2 = r2_score(y_test, gb_preds)
    print(f"   GB  → MAE: {gb_mae:.3f} pts | R²: {gb_r2:.4f}")

    # ── Ensemble (weighted average) ───────────────────────────────────────────
    w_rf = 1 / (rf_mae + 1e-9)
    w_gb = 1 / (gb_mae + 1e-9)
    w_total = w_rf + w_gb
    ensemble_preds = (w_rf * rf_preds + w_gb * gb_preds) / w_total
    ens_mae = mean_absolute_error(y_test, ensemble_preds)
    ens_r2  = r2_score(y_test, ensemble_preds)
    print(f"\n🎯 Ensemble → MAE: {ens_mae:.3f} pts | R²: {ens_r2:.4f}")

    # ── Feature importances (averaged) ───────────────────────────────────────
    fi = (rf.feature_importances_ * w_rf + gb.feature_importances_ * w_gb) / w_total
    importance_dict = dict(zip(FEATURE_NAMES, fi.tolist()))

    result = {
        "rf_model": rf,
        "gb_model": gb,
        "w_rf": w_rf,
        "w_gb": w_gb,
        "w_total": w_total,
        "feature_names": FEATURE_NAMES,
        "feature_importances": importance_dict,
        "eval": {
            "rf_mae": rf_mae, "rf_r2": rf_r2,
            "gb_mae": gb_mae, "gb_r2": gb_r2,
            "ensemble_mae": ens_mae, "ensemble_r2": ens_r2,
            "n_train": len(X_train), "n_test": len(X_test),
        }
    }

    print("\n📊 Top Feature Importances:")
    sorted_fi = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
    for feat, imp in sorted_fi[:6]:
        bar = "█" * int(imp * 40)
        print(f"   {feat:<28} {bar} {imp:.4f}")

    return result


def save_model(model_dict: Dict, path: str = "friction_model.pkl"):
    with open(path, "wb") as f:
        pickle.dump(model_dict, f)
    print(f"\n✅ Model saved → {path}")


def load_model(path: str = "friction_model.pkl") -> Dict:
    with open(path, "rb") as f:
        return pickle.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# 4. INFERENCE API  (called by logic.py)
# ─────────────────────────────────────────────────────────────────────────────

class FrictionScorer:
    """Thin wrapper around the trained ensemble for use in GlobalCapitalRouter."""

    def __init__(self, model_path: str = "friction_model.pkl"):
        self._model = load_model(model_path)

    def predict(
        self,
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
    ) -> Tuple[float, Dict]:
        """
        Returns (compliance_score 0-100, feature_importances dict).
        compliance_score = 100 - friction_score  (higher = better, matching original API)
        """
        fv = build_feature_vector(
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
        ).reshape(1, -1)

        m = self._model
        rf_pred = m["rf_model"].predict(fv)[0]
        gb_pred = m["gb_model"].predict(fv)[0]
        friction = float(np.clip(
            (m["w_rf"] * rf_pred + m["w_gb"] * gb_pred) / m["w_total"],
            0, 100
        ))
        compliance_score = round(100.0 - friction, 2)

        return compliance_score, m["feature_importances"]


# ─────────────────────────────────────────────────────────────────────────────
# 5. ENTRY POINT  (run this once to train + save model)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    model_dict = train_model("capital_routing_config.json")
    save_model(model_dict, "friction_model.pkl")
    print("\n🎉 Training complete. Use FrictionScorer('friction_model.pkl') in logic.py")
