from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.user import User, UserRole
from services.auth_service import get_password_hash


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(func.lower(User.email) == email.lower()).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    email: str,
    password: str,
    role: UserRole,
    is_active: bool = True,
) -> User:
    existing_user = get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    user = User(
        email=email,
        password_hash=get_password_hash(password),
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, target_user: User, updates: dict) -> User:
    if "email" in updates:
        existing_user = get_user_by_email(db, updates["email"])
        if existing_user and existing_user.id != target_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

    if "password" in updates:
        target_user.password_hash = get_password_hash(updates.pop("password"))

    for field, value in updates.items():
        setattr(target_user, field, value)

    db.commit()
    db.refresh(target_user)
    return target_user


def count_active_admins(db: Session) -> int:
    return (
        db.query(User)
        .filter(User.role == UserRole.ADMIN, User.is_active.is_(True))
        .count()
    )


def disable_user(db: Session, target_user: User) -> User:
    target_user.is_active = False
    db.commit()
    db.refresh(target_user)
    return target_user
