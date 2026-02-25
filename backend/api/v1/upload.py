"""
CSV Upload route: POST /upload/csv
Accepts multipart CSV, validates schema, runs batch inference, persists results.
"""

import uuid
from datetime import datetime, timezone
from io import StringIO

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, require_admin
from models.db_models import AuditLog, UploadBatch, User
from models.schemas import BatchError, UploadResponse
from services.ingestion import (
    deduplicate,
    process_batch,
    validate_csv_schema,
)

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/csv", response_model=UploadResponse)
async def upload_csv(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Upload a CSV of student records, validate schema, run batch predictions."""

    # File type check
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only .csv files are supported",
        )

    content = await file.read()

    # Parse CSV
    try:
        df = pd.read_csv(StringIO(content.decode("utf-8")))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not parse CSV: {e}")

    if df.empty:
        raise HTTPException(status_code=422, detail="Uploaded CSV file is empty")

    # Schema validation
    schema_errors = validate_csv_schema(df)
    if schema_errors:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "SCHEMA_MISMATCH",
                "message": f"CSV is missing required columns: {[e.field for e in schema_errors]}",
                "errors": [e.model_dump() for e in schema_errors],
            },
        )

    # Deduplicate
    df, n_dupes = deduplicate(df)
    total_rows = len(df)
    batch_id = str(uuid.uuid4())

    # Create UploadBatch record
    batch = UploadBatch(
        id=batch_id,
        uploaded_by=current_user.id,
        filename=file.filename,
        total_rows=total_rows,
        status="processing",
    )
    db.add(batch)
    await db.flush()

    # Process batch
    processed, error_count, errors = await process_batch(df, batch_id, db)

    # Update batch status
    batch.processed_rows = processed
    batch.error_rows     = error_count
    batch.status         = "done" if error_count == 0 else "failed" if processed == 0 else "done"
    batch.completed_at   = datetime.now(timezone.utc)
    if errors:
        batch.error_detail = [e.model_dump() for e in errors]

    # Audit
    db.add(AuditLog(
        user_id=current_user.id,
        action="UPLOAD_BATCH",
        detail={"batch_id": batch_id, "filename": file.filename, "total_rows": total_rows},
        ip_address=request.client.host if request.client else None,
    ))

    return UploadResponse(
        batch_id=batch_id,
        status=batch.status,
        total_rows=total_rows,
        processed_rows=processed,
        error_rows=error_count,
        errors=errors[:50],  # cap to 50 displayed errors
    )
