"""
Preprocessing service: encodes categoricals, imputes nulls, normalizes features.
Loads pre-fitted scaler and label encoders from ml/models/.
"""

import os
from typing import Any
import joblib
import numpy as np
import pandas as pd

from core.config import get_settings

settings = get_settings()

CATEGORICAL_FEATURES = ["gender", "department"]
REQUIRED_FIELDS = [
    "student_id", "age", "gender", "department", "semester",
    "attendance_pct", "assignment_score_avg", "internal_marks_avg",
    "semester_gpa", "study_hours_per_week", "participation_score",
    "prev_semester_gpa", "backlogs", "financial_aid",
]
NUMERIC_FEATURES = [
    "age", "semester", "attendance_pct", "assignment_score_avg",
    "internal_marks_avg", "semester_gpa", "study_hours_per_week",
    "participation_score", "prev_semester_gpa", "backlogs", "financial_aid",
]

_scaler = None
_label_encoders = None
_feature_names = None


def _load_artifacts():
    global _scaler, _label_encoders, _feature_names
    model_dir = settings.MODEL_DIR
    scaler_path = os.path.join(model_dir, "scaler.pkl")
    le_path    = os.path.join(model_dir, "label_encoders.pkl")
    fn_path    = os.path.join(model_dir, "feature_names.pkl")

    if os.path.exists(scaler_path):
        _scaler = joblib.load(scaler_path)
    if os.path.exists(le_path):
        _label_encoders = joblib.load(le_path)
    if os.path.exists(fn_path):
        _feature_names = joblib.load(fn_path)


def get_scaler():
    if _scaler is None:
        _load_artifacts()
    return _scaler


def get_label_encoders():
    if _label_encoders is None:
        _load_artifacts()
    return _label_encoders


def get_feature_names():
    if _feature_names is None:
        _load_artifacts()
    return _feature_names


def check_missing_ratio(record: dict) -> float:
    """Return ratio of missing fields (None/NaN) out of all required fields."""
    missing = 0
    for field in REQUIRED_FIELDS:
        val = record.get(field)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            missing += 1
    return missing / len(REQUIRED_FIELDS)


def preprocess_record(record: dict) -> np.ndarray:
    """
    Preprocesses a single student record dict into a scaled feature vector.
    Returns numpy array of shape (1, n_features).
    """
    label_encoders = get_label_encoders()
    scaler         = get_scaler()
    feature_names  = get_feature_names()

    row = {}
    for feat in REQUIRED_FIELDS:
        if feat == "student_id":
            continue
        val = record.get(feat)
        if val is None:
            # Impute with sensible defaults
            if feat in NUMERIC_FEATURES:
                val = 0.0
            else:
                val = "Unknown"
        row[feat] = val

    # Encode categoricals
    if label_encoders:
        for col in CATEGORICAL_FEATURES:
            le = label_encoders.get(col)
            if le:
                try:
                    row[col] = le.transform([str(row[col])])[0]
                except ValueError:
                    # Unseen label → use 0
                    row[col] = 0

    # financial_aid bool → int
    row["financial_aid"] = int(row.get("financial_aid", False))

    # Build feature vector in training order
    if feature_names:
        X = np.array([[row[f] for f in feature_names]], dtype=float)
    else:
        # Fallback order
        X = np.array([[
            row["age"], row["gender"], row["department"], row["semester"],
            row["attendance_pct"], row["assignment_score_avg"],
            row["internal_marks_avg"], row["semester_gpa"],
            row["study_hours_per_week"], row["participation_score"],
            row["prev_semester_gpa"], row["backlogs"], row["financial_aid"],
        ]], dtype=float)

    if scaler:
        X = scaler.transform(X)
    return X


def preprocess_dataframe(df: pd.DataFrame) -> np.ndarray:
    """Batch preprocess a Pandas DataFrame. Returns feature matrix."""
    results = []
    for _, row in df.iterrows():
        X = preprocess_record(row.to_dict())
        results.append(X[0])
    return np.array(results)
