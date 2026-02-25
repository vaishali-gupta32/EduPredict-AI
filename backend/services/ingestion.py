"""
CSV ingestion service: parse, validate schema, deduplicate, batch predict, persist.
"""

import uuid
from datetime import datetime, timezone
from io import StringIO
from typing import Any

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.db_models import Student, Prediction, UploadBatch
from models.schemas import BatchError
from services.preprocessing import check_missing_ratio, preprocess_record, REQUIRED_FIELDS
from services.inference import predict_single
from services.intervention import get_interventions

REQUIRED_CSV_COLUMNS = [f for f in REQUIRED_FIELDS if f != "student_id"] + ["student_id"]
OPTIONAL_OUTPUT_COLS = {"performance_category"}  # may appear in uploaded CSV from training data


def validate_csv_schema(df: pd.DataFrame) -> list[BatchError]:
    """Check that all required columns are present and return list of errors."""
    errors = []
    missing = [c for c in REQUIRED_CSV_COLUMNS if c not in df.columns]
    for col in missing:
        errors.append(BatchError(row=0, field=col, error=f"Missing required column: '{col}'"))
    return errors


def deduplicate(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Keep last occurrence per student_id. Returns (df, n_dupes_dropped)."""
    before = len(df)
    df = df.drop_duplicates(subset=["student_id"], keep="last").reset_index(drop=True)
    return df, before - len(df)


async def process_batch(
    df: pd.DataFrame,
    batch_id: str,
    db: AsyncSession,
) -> tuple[int, int, list[BatchError]]:
    """
    For each row: preprocess → predict → get interventions → upsert student → insert prediction.
    Returns (processed_rows, error_rows, errors).
    """
    processed = 0
    error_count = 0
    errors: list[BatchError] = []

    for row_idx, row in df.iterrows():
        record = row.to_dict()
        student_id = str(record.get("student_id", "")).strip()

        try:
            # Missing data check
            missing_ratio = check_missing_ratio(record)
            if missing_ratio > 0.30:
                errors.append(BatchError(
                    row=int(row_idx) + 2,
                    error=f"Student {student_id} has {missing_ratio:.0%} missing fields — skipped"
                ))
                error_count += 1
                continue

            # Preprocess
            X = preprocess_record(record)

            # Predict
            pred = predict_single(X, record)

            # Interventions
            interventions = get_interventions(record, pred["dropout_probability"])

            # Upsert Student
            result = await db.execute(select(Student).where(Student.student_id == student_id))
            student = result.scalar_one_or_none()
            if student is None:
                student = Student(
                    student_id=student_id,
                    age=record.get("age"),
                    gender=str(record.get("gender", "")),
                    department=str(record.get("department", "")),
                    semester=record.get("semester"),
                )
                db.add(student)
            else:
                student.age        = record.get("age", student.age)
                student.gender     = str(record.get("gender", student.gender))
                student.department = str(record.get("department", student.department))
                student.semester   = record.get("semester", student.semester)
                student.updated_at = datetime.now(timezone.utc)

            # Insert Prediction
            prediction = Prediction(
                student_id=student_id,
                attendance_pct=record.get("attendance_pct"),
                assignment_score_avg=record.get("assignment_score_avg"),
                internal_marks_avg=record.get("internal_marks_avg"),
                semester_gpa=record.get("semester_gpa"),
                study_hours_per_week=record.get("study_hours_per_week"),
                participation_score=record.get("participation_score"),
                prev_semester_gpa=record.get("prev_semester_gpa"),
                backlogs=record.get("backlogs"),
                financial_aid=bool(record.get("financial_aid", False)),
                performance_category=pred["performance_category"],
                dropout_probability=pred["dropout_probability"],
                confidence_score=pred["confidence"],
                top_factors=pred["top_factors"],
                recommended_interventions=interventions,
                model_version=pred["model_version"],
                batch_upload_id=batch_id,
            )
            db.add(prediction)

            processed += 1

        except Exception as e:
            errors.append(BatchError(
                row=int(row_idx) + 2,
                error=str(e)
            ))
            error_count += 1

    await db.flush()
    return processed, error_count, errors
