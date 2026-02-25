"""
Student routes: GET /students (filtered/paginated), GET /students/{student_id}
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from models.db_models import AuditLog, Prediction, Student, User
from models.schemas import (
    PredictionHistoryItem, PredictionResponse, StudentDetail,
    StudentListItem, StudentListResponse, TopFactor
)

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=StudentListResponse)
async def list_students(
    risk: str | None = Query(None, description="Filter by performance category: High | Medium | At Risk"),
    department: str | None = Query(None),
    semester: int | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns paginated student list with their latest prediction.
    Filterable by risk category, department, and semester.
    """
    # Subquery: latest prediction per student
    latest_pred_subq = (
        select(
            Prediction.student_id,
            func.max(Prediction.predicted_at).label("max_pred_at"),
        )
        .group_by(Prediction.student_id)
        .subquery()
    )

    # Join students → latest prediction
    stmt = (
        select(Student, Prediction)
        .join(
            latest_pred_subq,
            Student.student_id == latest_pred_subq.c.student_id,
            isouter=True,
        )
        .join(
            Prediction,
            (Prediction.student_id == latest_pred_subq.c.student_id) &
            (Prediction.predicted_at == latest_pred_subq.c.max_pred_at),
            isouter=True,
        )
    )

    # Filters
    if department:
        stmt = stmt.where(Student.department == department)
    if semester:
        stmt = stmt.where(Student.semester == semester)
    if risk:
        stmt = stmt.where(Prediction.performance_category == risk)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Paginate
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    result = await db.execute(stmt)
    rows = result.all()

    data = []
    for row in rows:
        student, pred = row
        data.append(StudentListItem(
            student_id=student.student_id,
            department=student.department,
            semester=student.semester,
            performance_category=pred.performance_category if pred else None,
            dropout_probability=pred.dropout_probability if pred else None,
            predicted_at=pred.predicted_at if pred else None,
        ))

    return StudentListResponse(total=total, page=page, limit=limit, data=data)


@router.get("/{student_id}", response_model=StudentDetail)
async def get_student(
    student_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns full student record with latest prediction and prediction history."""
    result = await db.execute(select(Student).where(Student.student_id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found")

    # Prediction history (latest first)
    pred_result = await db.execute(
        select(Prediction)
        .where(Prediction.student_id == student_id)
        .order_by(Prediction.predicted_at.desc())
        .limit(20)
    )
    predictions = pred_result.scalars().all()

    latest = predictions[0] if predictions else None
    latest_pred_resp = None
    if latest:
        factors = [TopFactor(**f) for f in (latest.top_factors or [])]
        latest_pred_resp = PredictionResponse(
            student_id=student_id,
            performance_category=latest.performance_category,
            dropout_probability=latest.dropout_probability,
            confidence=latest.confidence_score or 0.0,
            top_factors=factors,
            recommended_interventions=latest.recommended_interventions or [],
            data_quality_flag=latest.data_quality_flag,
            model_version=latest.model_version,
            predicted_at=latest.predicted_at,
        )

    # Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        student_id=student_id,
        action="VIEW_STUDENT",
        ip_address=request.client.host if request.client else None,
    ))

    return StudentDetail(
        student_id=student.student_id,
        age=student.age,
        gender=student.gender,
        department=student.department,
        semester=student.semester,
        latest_prediction=latest_pred_resp,
        prediction_history=[PredictionHistoryItem.model_validate(p) for p in predictions[1:]],
    )
