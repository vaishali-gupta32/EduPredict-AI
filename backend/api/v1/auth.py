"""
Auth API routes: POST /auth/login, GET /auth/me
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from core.security import create_access_token, verify_password
from models.db_models import AuditLog, User
from models.schemas import LoginRequest, TokenResponse, UserOut
from core.config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == body.email))
    user: User | None = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})

    # Audit log
    db.add(AuditLog(
        user_id=user.id,
        action="LOGIN",
        ip_address=request.client.host if request.client else None,
    ))

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
