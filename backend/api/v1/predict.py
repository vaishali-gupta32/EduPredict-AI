"""
Prediction routes: POST /predict (single), POST /predict/batch (JSON array)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from models.db_models import AuditLog, Prediction, Student, User
from models.schemas import PredictionResponse, StudentInput, TopFactor
from services.inference import predict_single
from services.intervention import get_interventions
from services.preprocessing import check_missing_ratio, preprocess_record

router = APIRouter(prefix="/predict", tags=["Predictions"])


async def _run_and_persist(
    student_data: StudentInput,
    db: AsyncSession,
    current_user: User,
    request: Request,
) -> PredictionResponse:
    record = student_data.model_dump()
    student_id = record["student_id"]

    # Missing data check
    missing_ratio = check_missing_ratio(record)
    quality_flag = "INSUFFICIENT_DATA" if missing_ratio > 0.30 else None

    if quality_flag:
        raise HTTPException(
            status_code=422,
            detail=f"Student {student_id} has too many missing fields ({missing_ratio:.0%}). "
                   "Minimum 70% of fields required.",
        )

    X = preprocess_record(record)
    pred = predict_single(X, record)
    interventions = get_interventions(record, pred["dropout_probability"])

    # Upsert student
    result = await db.execute(select(Student).where(Student.student_id == student_id))
    student = result.scalar_one_or_none()
    if student is None:
        student = Student(
            student_id=student_id,
            age=record.get("age"),
            gender=record.get("gender"),
            department=record.get("department"),
            semester=record.get("semester"),
        )
        db.add(student)
    else:
        student.updated_at = datetime.now(timezone.utc)

    # Insert prediction
    prediction_row = Prediction(
        student_id=student_id,
        attendance_pct=record.get("attendance_pct"),
        assignment_score_avg=record.get("assignment_score_avg"),
        internal_marks_avg=record.get("internal_marks_avg"),
        semester_gpa=record.get("semester_gpa"),
        study_hours_per_week=record.get("study_hours_per_week"),
        participation_score=record.get("participation_score"),
        prev_semester_gpa=record.get("prev_semester_gpa"),
        backlogs=record.get("backlogs"),
        financial_aid=record.get("financial_aid"),
        performance_category=pred["performance_category"],
        dropout_probability=pred["dropout_probability"],
        confidence_score=pred["confidence"],
        top_factors=pred["top_factors"],
        recommended_interventions=interventions,
        model_version=pred["model_version"],
    )
    db.add(prediction_row)

    # Audit
    db.add(AuditLog(
        user_id=current_user.id,
        student_id=student_id,
        action="GET_PREDICTION",
        detail={"performance_category": pred["performance_category"]},
        ip_address=request.client.host if request.client else None,
    ))

    await db.flush()

    return PredictionResponse(
        student_id=student_id,
        performance_category=pred["performance_category"],
        dropout_probability=pred["dropout_probability"],
        confidence=pred["confidence"],
        top_factors=[TopFactor(**f) for f in pred["top_factors"]],
        recommended_interventions=interventions,
        data_quality_flag=quality_flag,
        model_version=pred["model_version"],
        predicted_at=datetime.now(timezone.utc),
    )


@router.post("", response_model=PredictionResponse)
async def predict(
    student: StudentInput,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Single student prediction with DB persistence."""
    return await _run_and_persist(student, db, current_user, request)


@router.post("/batch", response_model=list[PredictionResponse])
async def predict_batch(
    students: list[StudentInput],
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Batch JSON prediction for a list of students."""
    if len(students) > 500:
        raise HTTPException(status_code=400, detail="Batch size limit is 500 per request. Use CSV upload for larger batches.")

    results = []
    for s in students:
        try:
            r = await _run_and_persist(s, db, current_user, request)
            results.append(r)
        except HTTPException:
            continue
    return results
