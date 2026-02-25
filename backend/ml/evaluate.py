"""
Standalone model evaluation utilities.
Used by train.py and surfaced via the /model/metrics API endpoint.
"""

import json
import os
import numpy as np
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score,
    recall_score, roc_auc_score, confusion_matrix
)

MODEL_REGISTRY_PATH = os.environ.get(
    "MODEL_REGISTRY_PATH", "./ml/models/model_registry.json"
)


def compute_metrics(y_true, y_pred, y_proba=None) -> dict:
    """
    Compute full classification metrics.
    Returns a dict compatible with ModelMetricsResponse schema.
    """
    acc        = accuracy_score(y_true, y_pred)
    f1_ar      = f1_score(y_true, y_pred, labels=[2], average="macro", zero_division=0)
    f1_macro   = f1_score(y_true, y_pred, average="macro", zero_division=0)
    prec_ar    = precision_score(y_true, y_pred, labels=[2], average="macro", zero_division=0)
    rec_ar     = recall_score(y_true, y_pred, labels=[2], average="macro", zero_division=0)
    cm         = confusion_matrix(y_true, y_pred).tolist()

    roc = 0.0
    if y_proba is not None:
        try:
            roc = roc_auc_score(y_true, y_proba, multi_class="ovr", average="macro")
        except Exception:
            pass

    return {
        "accuracy":        round(float(acc), 4),
        "roc_auc":         round(float(roc), 4),
        "f1_at_risk":      round(float(f1_ar), 4),
        "f1_macro":        round(float(f1_macro), 4),
        "precision_score": round(float(prec_ar), 4),
        "recall_score":    round(float(rec_ar), 4),
        "confusion_matrix": cm,
    }


def load_registry() -> dict:
    """Load and return the model registry JSON."""
    path = os.environ.get("MODEL_REGISTRY_PATH", MODEL_REGISTRY_PATH)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def detect_drift(metrics: dict) -> bool:
    """
    Simple rule-based drift detection.
    Returns True if accuracy or ROC-AUC falls below acceptable threshold.
    """
    return (
        metrics.get("accuracy", 1.0) < 0.70 or
        metrics.get("roc_auc", 1.0) < 0.70
    )
