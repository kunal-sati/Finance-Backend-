from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_user
from middleware.rate_limit import limit_requests
from models.user import User, UserRole
from schemas.auth import LoginRequest, TokenResponse
from schemas.user import UserOut, UserRegister
from services.auth_service import authenticate_user, create_access_token, create_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserRegister,
    db: Session = Depends(get_db),
    _: None = Depends(limit_requests(bucket="auth_register", limit=5, window_seconds=60)),
):
    first_user_exists = db.query(User.id).first() is not None
    assigned_role = UserRole.VIEWER if first_user_exists else UserRole.ADMIN

    return create_user(
        db=db,
        email=payload.email,
        password=payload.password,
        role=assigned_role,
        is_active=True,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    _: None = Depends(limit_requests(bucket="auth_login", limit=5, window_seconds=60)),
):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    token = create_access_token(
        {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
        }
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
