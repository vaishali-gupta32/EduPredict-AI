"""
ML Training Script
Trains Logistic Regression, Random Forest, XGBoost, LightGBM on student data.
Auto-selects champion model by F1 score on the "At Risk" class.
Saves all artifacts to ml/models/ and writes model_registry.json.

Run from backend/ directory:
    python ml/train.py
"""

import os
import sys
import json
import joblib
import warnings
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score,
    recall_score, roc_auc_score, confusion_matrix
)

import xgboost as xgb
import lightgbm as lgb

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Support both backend/data/ and project_root/data/ locations
_data_local  = os.path.join(BASE_DIR, "data", "students.csv")
_data_parent = os.path.join(BASE_DIR, "..", "data", "students.csv")
DATA_PATH    = _data_local if os.path.exists(_data_local) else _data_parent
MODEL_DIR   = os.path.join(BASE_DIR, "ml", "models")
REGISTRY    = os.path.join(MODEL_DIR, "model_registry.json")

LABEL_COL            = "performance_category"
CATEGORICAL_FEATURES = ["gender", "department"]
DROP_COLS            = ["student_id", "performance_category"]
LABEL_MAP            = {"High": 0, "Medium": 1, "At Risk": 2}
LABEL_MAP_INV        = {v: k for k, v in LABEL_MAP.items()}

os.makedirs(MODEL_DIR, exist_ok=True)


# ── Data Loading & Preprocessing ───────────────────────────────────────────────
def load_and_preprocess(path: str):
    df = pd.read_csv(path)
    print(f"📂 Loaded {len(df)} records from {path}")

    # Encode categoricals
    label_encoders = {}
    for col in CATEGORICAL_FEATURES:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le

    # Encode boolean
    df["financial_aid"] = df["financial_aid"].astype(int)

    # Target label
    y = df[LABEL_COL].map(LABEL_MAP).values
    X = df.drop(columns=DROP_COLS).values
    feature_names = [c for c in df.columns if c not in DROP_COLS]

    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y, scaler, label_encoders, feature_names


# ── Evaluation ─────────────────────────────────────────────────────────────────
def evaluate_model(model, X_test, y_test, model_name: str):
    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    acc      = accuracy_score(y_test, y_pred)
    f1_ar    = f1_score(y_test, y_pred, labels=[2], average="macro")
    prec_ar  = precision_score(y_test, y_pred, labels=[2], average="macro", zero_division=0)
    rec_ar   = recall_score(y_test, y_pred, labels=[2], average="macro", zero_division=0)
    f1_macro = f1_score(y_test, y_pred, average="macro")
    cm       = confusion_matrix(y_test, y_pred).tolist()

    try:
        roc = roc_auc_score(y_test, y_proba, multi_class="ovr", average="macro")
    except Exception:
        roc = 0.0

    metrics = {
        "model_name":      model_name,
        "accuracy":        round(acc, 4),
        "roc_auc":         round(roc, 4),
        "f1_at_risk":      round(f1_ar, 4),
        "f1_macro":        round(f1_macro, 4),
        "precision_score": round(prec_ar, 4),
        "recall_score":    round(rec_ar, 4),
        "confusion_matrix": cm,
    }

    print(f"\n  [{model_name}]")
    print(f"    Accuracy : {acc:.4f}")
    print(f"    ROC-AUC  : {roc:.4f}")
    print(f"    F1 (All) : {f1_macro:.4f}")
    print(f"    F1(AtRsk): {f1_ar:.4f}")
    print(f"    Precision: {prec_ar:.4f}  Recall: {rec_ar:.4f}")
    return metrics


# ── Training ───────────────────────────────────────────────────────────────────
def train():
    print("\n🚀 Starting ML Training Pipeline\n" + "="*50)

    X, y, scaler, label_encoders, feature_names = load_and_preprocess(DATA_PATH)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )
    print(f"  Train: {len(X_train)} | Test: {len(X_test)}")
    print(f"  Class dist (train): {np.bincount(y_train.astype(int))}")

    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
        "RandomForest":       RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
        "XGBoost":            xgb.XGBClassifier(
                                  n_estimators=200, learning_rate=0.1,
                                  max_depth=6, use_label_encoder=False,
                                  eval_metric="mlogloss", random_state=42, verbosity=0
                              ),
        "LightGBM":           lgb.LGBMClassifier(
                                  n_estimators=200, learning_rate=0.1,
                                  max_depth=6, random_state=42, verbose=-1
                              ),
    }

    print("\n📊 Training & Evaluating Models:")
    all_metrics  = []
    trained_models = {}

    for name, clf in models.items():
        clf.fit(X_train, y_train)
        m = evaluate_model(clf, X_test, y_test, name)
        all_metrics.append(m)
        trained_models[name] = clf

    # ── Champion selection (best F1 on "At Risk") ──────────────────────────────
    best = max(all_metrics, key=lambda m: m["f1_at_risk"])
    best_model = trained_models[best["model_name"]]
    print(f"\n🏆 Champion Model: {best['model_name']} (F1 At-Risk={best['f1_at_risk']:.4f})")

    # ── Save artifacts ─────────────────────────────────────────────────────────
    joblib.dump(best_model,  os.path.join(MODEL_DIR, "champion_model.pkl"))
    joblib.dump(scaler,      os.path.join(MODEL_DIR, "scaler.pkl"))
    joblib.dump(label_encoders, os.path.join(MODEL_DIR, "label_encoders.pkl"))
    joblib.dump(feature_names,  os.path.join(MODEL_DIR, "feature_names.pkl"))

    # Also save all models for reference
    for name, clf in trained_models.items():
        safe_name = name.lower().replace(" ", "_")
        joblib.dump(clf, os.path.join(MODEL_DIR, f"{safe_name}.pkl"))

    # ── Write registry ─────────────────────────────────────────────────────────
    registry = {
        "champion": {
            **best,
            "model_version": "v1.0",
            "is_champion":   True,
            "trained_at":    datetime.utcnow().isoformat() + "Z",
            "feature_names": feature_names,
            "label_map":     LABEL_MAP_INV,
        },
        "all_models": all_metrics,
    }
    with open(REGISTRY, "w") as f:
        json.dump(registry, f, indent=2)

    print(f"\n✅ Artifacts saved to {MODEL_DIR}")
    print(f"✅ Registry written to {REGISTRY}")
    print("\nMinimum threshold check:")
    print(f"  Accuracy ≥ 0.80 : {'✅' if best['accuracy'] >= 0.80 else '❌'} ({best['accuracy']})")
    print(f"  ROC-AUC  ≥ 0.80 : {'✅' if best['roc_auc'] >= 0.80 else '❌'} ({best['roc_auc']})")
    print(f"  F1(Risk) ≥ 0.75 : {'✅' if best['f1_at_risk'] >= 0.75 else '❌'} ({best['f1_at_risk']})")


if __name__ == "__main__":
    train()
