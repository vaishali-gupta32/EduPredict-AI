"""
SQLAlchemy ORM models for all 6 database tables.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON, Boolean, Column, DateTime, Float,
    ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import relationship

from db.session import Base


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


# ── Users ──────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id            = Column(String(36), primary_key=True, default=_uuid)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name     = Column(String(255))
    role          = Column(String(20), nullable=False, default="viewer")  # admin | viewer
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), default=_now)
    updated_at    = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    audit_logs    = relationship("AuditLog", back_populates="user", lazy="select")
    upload_batches = relationship("UploadBatch", back_populates="uploaded_by_user", lazy="select")


# ── Students ───────────────────────────────────────────────────────────────────
class Student(Base):
    __tablename__ = "students"

    id         = Column(String(36), primary_key=True, default=_uuid)
    student_id = Column(String(50), unique=True, nullable=False, index=True)
    age        = Column(Integer)
    gender     = Column(String(20))
    department = Column(String(50), index=True)
    semester   = Column(Integer, index=True)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    predictions = relationship("Prediction", back_populates="student", lazy="select",
                               order_by="Prediction.predicted_at.desc()")


# ── Predictions ────────────────────────────────────────────────────────────────
class Prediction(Base):
    __tablename__ = "predictions"

    id                       = Column(String(36), primary_key=True, default=_uuid)
    student_id               = Column(String(50), ForeignKey("students.student_id", ondelete="CASCADE"),
                                      nullable=False, index=True)

    # Raw feature snapshot
    attendance_pct           = Column(Float)
    assignment_score_avg     = Column(Float)
    internal_marks_avg       = Column(Float)
    semester_gpa             = Column(Float)
    study_hours_per_week     = Column(Float)
    participation_score      = Column(Float)
    prev_semester_gpa        = Column(Float)
    backlogs                 = Column(Integer)
    financial_aid            = Column(Boolean)

    # Prediction outputs
    performance_category     = Column(String(20), nullable=False, index=True)
    dropout_probability      = Column(Float, nullable=False)
    confidence_score         = Column(Float)
    top_factors              = Column(JSON)   # list[{feature, impact, value}]
    recommended_interventions = Column(JSON)  # list[str]
    data_quality_flag        = Column(String(30))  # None | "INSUFFICIENT_DATA"

    # Metadata
    model_version            = Column(String(50))
    batch_upload_id          = Column(String(36), index=True)
    predicted_at             = Column(DateTime(timezone=True), default=_now, index=True)

    student = relationship("Student", back_populates="predictions")


# ── Audit Logs ─────────────────────────────────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id         = Column(String(36), primary_key=True, default=_uuid)
    user_id    = Column(String(36), ForeignKey("users.id"), nullable=True)
    student_id = Column(String(50), nullable=True)
    action     = Column(String(50), nullable=False)  # VIEW_STUDENT | UPLOAD_BATCH | GET_PREDICTION
    detail     = Column(JSON)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), default=_now)

    user = relationship("User", back_populates="audit_logs")


# ── Upload Batches ─────────────────────────────────────────────────────────────
class UploadBatch(Base):
    __tablename__ = "upload_batches"

    id             = Column(String(36), primary_key=True, default=_uuid)
    uploaded_by    = Column(String(36), ForeignKey("users.id"), nullable=True)
    filename       = Column(String(255))
    total_rows     = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    error_rows     = Column(Integer, default=0)
    status         = Column(String(20), default="pending")  # pending|processing|done|failed
    error_detail   = Column(JSON)
    created_at     = Column(DateTime(timezone=True), default=_now)
    completed_at   = Column(DateTime(timezone=True))

    uploaded_by_user = relationship("User", back_populates="upload_batches")


# ── Model Registry ─────────────────────────────────────────────────────────────
class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id               = Column(String(36), primary_key=True, default=_uuid)
    model_name       = Column(String(100))
    model_version    = Column(String(50))
    accuracy         = Column(Float)
    roc_auc          = Column(Float)
    f1_at_risk       = Column(Float)
    precision_score  = Column(Float)
    recall_score     = Column(Float)
    confusion_matrix = Column(JSON)
    is_champion      = Column(Boolean, default=False)
    trained_at       = Column(DateTime(timezone=True), default=_now)
