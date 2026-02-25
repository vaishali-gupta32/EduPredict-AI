"""
Model health route: GET /model/metrics
Returns champion model metrics + drift detection flag.
"""

import json
import os

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.dependencies import get_current_user, get_db
from ml.evaluate import detect_drift, load_registry
from models.db_models import User
from models.schemas import ModelMetricsResponse

router = APIRouter(prefix="/model", tags=["Model Health"])
settings = get_settings()


@router.get("/metrics", response_model=ModelMetricsResponse)
async def get_model_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns current champion model metrics and drift warning flag."""
    registry = load_registry()

    if not registry:
        return ModelMetricsResponse(
            model_name="N/A",
            model_version="N/A",
            accuracy=0.0,
            roc_auc=0.0,
            f1_at_risk=0.0,
            precision=0.0,
            recall=0.0,
            confusion_matrix=[],
            model_drift_warning=True,
            trained_at=None,
        )

    champion = registry.get("champion", {})
    drift = detect_drift(champion)

    return ModelMetricsResponse(
        model_name=champion.get("model_name", "Unknown"),
        model_version=champion.get("model_version", "v1.0"),
        accuracy=champion.get("accuracy", 0.0),
        roc_auc=champion.get("roc_auc", 0.0),
        f1_at_risk=champion.get("f1_at_risk", 0.0),
        f1_macro=champion.get("f1_macro"),
        precision=champion.get("precision_score", 0.0),
        recall=champion.get("recall_score", 0.0),
        confusion_matrix=champion.get("confusion_matrix", []),
        model_drift_warning=drift,
        trained_at=champion.get("trained_at"),
    )
