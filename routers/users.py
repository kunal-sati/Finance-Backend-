from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import require_roles
from middleware.rate_limit import limit_requests
from models.user import User, UserRole
from schemas.user import UserCreate, UserOut, UserUpdate
from services.auth_service import count_active_admins, create_user, get_user_by_id, update_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
    __: None = Depends(limit_requests(bucket="users_write", limit=30, window_seconds=60)),
):
    return create_user(
        db=db,
        email=payload.email,
        password=payload.password,
        role=payload.role,
        is_active=payload.is_active,
    )


@router.get("/", response_model=list[UserOut])
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    return db.query(User).order_by(User.id.asc()).offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user_endpoint(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
    __: None = Depends(limit_requests(bucket="users_write", limit=30, window_seconds=60)),
):
    target_user = get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update fields provided",
        )

    will_remove_admin_privileges = (
        target_user.role == UserRole.ADMIN
        and (
            updates.get("role") not in (None, UserRole.ADMIN)
            or updates.get("is_active") is False
        )
    )
    if will_remove_admin_privileges and count_active_admins(db) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one active admin must remain",
        )

    return update_user(db, target_user, updates)