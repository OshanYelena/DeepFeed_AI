"""
DeepFeed AI - Auth Routes (M1)
POST /auth/register
POST /auth/login
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.connection import get_db
from application.services.auth_service import AuthService
from application.dtos.user_dtos import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse
from api.schemas import success_response, error_response
from logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    service = AuthService(db)
    try:
        user = await service.register(request, trace_id)
        await db.commit()
        return success_response(
            RegisterResponse(user_id=user.id, message="User registered successfully").model_dump(),
            trace_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response("CONFLICT", str(e), trace_id),
        )


@router.post("/login")
async def login(
    request: LoginRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    service = AuthService(db)
    try:
        access_token, refresh_token = await service.login(request, trace_id)
        return success_response(
            LoginResponse(access_token=access_token, refresh_token=refresh_token).model_dump(),
            trace_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("UNAUTHORIZED", str(e), trace_id),
        )
