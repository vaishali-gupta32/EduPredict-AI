"""
Inference service: loads champion model at startup (singleton),
runs predict_proba, computes SHAP values, returns structured predictions.
"""

import json
import os
from typing import Optional
import joblib
import numpy as np
import shap

from core.config import get_settings
from models.schemas import PredictionResponse, TopFactor

settings = get_settings()

LABEL_MAP_INV = {0: "High", 1: "Medium", 2: "At Risk"}
IMPACT_THRESHOLDS = {"HIGH": 0.3, "MEDIUM": 0.1}

# Singleton state (loaded once at startup via lifespan)
_model = None
_explainer = None
_model_version = "v1.0"
_feature_names: list[str] = []


def load_champion_model():
    """
    Load champion model + scaler from ml/models/.
    Called once at application startup.
    """
    global _model, _explainer, _model_version, _feature_names

    registry_path = settings.MODEL_REGISTRY_PATH
    model_dir     = settings.MODEL_DIR

    if os.path.exists(registry_path):
        with open(registry_path, "r") as f:
            registry = json.load(f)
        champion = registry.get("champion", {})
        _model_version = champion.get("model_version", "v1.0")
        _feature_names = champion.get("feature_names", [])

    model_path = os.path.join(model_dir, "champion_model.pkl")
    if os.path.exists(model_path):
        _model = joblib.load(model_path)
        # Build SHAP explainer once
        try:
            _explainer = shap.TreeExplainer(_model)
        except Exception:
            _explainer = None
        print(f"✅ Champion model loaded: {_model_version}")
    else:
        print("⚠️  No trained model found. Run ml/train.py first.")


def get_model():
    return _model


def get_explainer():
    return _explainer


def _get_impact_label(abs_val: float, total: float) -> str:
    ratio = abs_val / (total + 1e-9)
    if ratio >= IMPACT_THRESHOLDS["HIGH"]:
        return "HIGH"
    elif ratio >= IMPACT_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "LOW"


def get_top_shap_factors(shap_values: np.ndarray, raw_record: dict, n: int = 3) -> list[TopFactor]:
    """
    Compute top-n SHAP factors for the predicted class.
    Returns list of TopFactor dicts.
    """
    names = _feature_names if _feature_names else list(raw_record.keys())
    abs_vals = np.abs(shap_values)
    total = abs_vals.sum()

    top_indices = np.argsort(abs_vals)[::-1][:n]

    factors = []
    for idx in top_indices:
        if idx >= len(names):
            continue
        feat_name = names[idx]
        abs_v     = float(abs_vals[idx])
        raw_val   = raw_record.get(feat_name, 0.0)
        impact    = _get_impact_label(abs_v, total)
        factors.append(TopFactor(
            feature=feat_name,
            impact=impact,
            value=float(raw_val) if isinstance(raw_val, (int, float, np.floating)) else 0.0,
        ))
    return factors


def predict_single(X: np.ndarray, raw_record: dict) -> dict:
    """
    Run inference on a single preprocessed feature vector.
    Returns prediction dict matching PredictionResponse schema.
    """
    model     = get_model()
    explainer = get_explainer()

    if model is None:
        raise RuntimeError("Model not loaded. Run ml/train.py first.")

    proba    = model.predict_proba(X)[0]  # shape: (3,)
    pred_idx = int(np.argmax(proba))
    category = LABEL_MAP_INV[pred_idx]
    dropout_prob = float(proba[2])  # index 2 = "At Risk" probability
    confidence   = float(proba[pred_idx])

    # SHAP
    top_factors = []
    if explainer is not None:
        try:
            sv = explainer.shap_values(X)
            # sv may be list (one per class) or ndarray
            if isinstance(sv, list):
                class_shap = sv[pred_idx][0]
            else:
                class_shap = sv[pred_idx] if sv.ndim == 2 else sv[0]
            top_factors = get_top_shap_factors(class_shap, raw_record)
        except Exception as e:
            print(f"SHAP warning: {e}")

    return {
        "performance_category": category,
        "dropout_probability":  round(dropout_prob, 4),
        "confidence":           round(confidence, 4),
        "top_factors":          [f.model_dump() for f in top_factors],
        "model_version":        _model_version,
    }
