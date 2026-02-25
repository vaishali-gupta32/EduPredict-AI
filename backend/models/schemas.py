"""
Pydantic v2 schemas: all request/response models for every API endpoint.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool


# ── Student Input ─────────────────────────────────────────────────────────────
class StudentInput(BaseModel):
    student_id: str
    age: int = Field(..., ge=15, le=60)
    gender: str
    department: str
    semester: int = Field(..., ge=1, le=8)
    attendance_pct: float = Field(..., ge=0, le=100)
    assignment_score_avg: float = Field(..., ge=0, le=100)
    internal_marks_avg: float = Field(..., ge=0, le=100)
    semester_gpa: float = Field(..., ge=0, le=10)
    study_hours_per_week: float = Field(..., ge=0, le=168)
    participation_score: float = Field(..., ge=0, le=10)
    prev_semester_gpa: float = Field(..., ge=0, le=10)
    backlogs: int = Field(..., ge=0)
    financial_aid: bool


# ── Prediction Output ─────────────────────────────────────────────────────────
class TopFactor(BaseModel):
    feature: str
    impact: str   # HIGH | MEDIUM | LOW
    value: float


class PredictionResponse(BaseModel):
    student_id: str
    performance_category: str
    dropout_probability: float
    confidence: float
    top_factors: list[TopFactor]
    recommended_interventions: list[str]
    data_quality_flag: Optional[str] = None
    model_version: Optional[str] = None
    predicted_at: Optional[datetime] = None


# ── Student List ──────────────────────────────────────────────────────────────
class StudentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    student_id: str
    department: Optional[str] = None
    semester: Optional[int] = None
    performance_category: Optional[str] = None
    dropout_probability: Optional[float] = None
    predicted_at: Optional[datetime] = None


class StudentListResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: list[StudentListItem]


class PredictionHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    performance_category: str
    dropout_probability: float
    top_factors: Optional[Any] = None
    recommended_interventions: Optional[Any] = None
    data_quality_flag: Optional[str] = None
    model_version: Optional[str] = None
    predicted_at: Optional[datetime] = None


class StudentDetail(BaseModel):
    student_id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[int] = None
    latest_prediction: Optional[PredictionResponse] = None
    prediction_history: list[PredictionHistoryItem] = []


# ── Upload ────────────────────────────────────────────────────────────────────
class BatchError(BaseModel):
    row: int
    field: Optional[str] = None
    error: str


class UploadResponse(BaseModel):
    batch_id: str
    status: str
    total_rows: int
    processed_rows: int
    error_rows: int
    errors: list[BatchError] = []


# ── Model Health ──────────────────────────────────────────────────────────────
class ModelMetricsResponse(BaseModel):
    model_name: str
    model_version: str
    accuracy: float
    roc_auc: float
    f1_at_risk: float
    f1_macro: Optional[float] = None
    precision: float
    recall: float
    confusion_matrix: list[list[int]]
    model_drift_warning: bool = False
    trained_at: Optional[str] = None


# ── Error ─────────────────────────────────────────────────────────────────────
class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int
