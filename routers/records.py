from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import require_roles
from middleware.rate_limit import limit_requests
from models.record import RecordType
from models.user import User, UserRole
from schemas.record import RecordCreate, RecordOut, RecordUpdate
from services.record_service import (
    create_record,
    delete_record,
    get_record_or_404,
    list_records,
    update_record,
)

router = APIRouter(prefix="/records", tags=["Records"])

@router.post("/", response_model=RecordOut, status_code=status.HTTP_201_CREATED)
def create_record_endpoint(
    payload: RecordCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
    __: None = Depends(limit_requests(bucket="records_write", limit=60, window_seconds=60)),
):
    return create_record(db, payload, payload.user_id)


@router.get("/", response_model=list[RecordOut])
def list_records_endpoint(
    record_type: RecordType | None = Query(default=None),
    category: str | None = Query(default=None, min_length=1, max_length=64),
    search: str | None = Query(default=None, min_length=1, max_length=100),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date",
        )

    return list_records(
        db=db,
        record_type=record_type,
        category=category,
        search=search,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )


@router.get("/{record_id}", response_model=RecordOut)
def get_record_endpoint(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
):
    return get_record_or_404(db, record_id)


@router.patch("/{record_id}", response_model=RecordOut)
def update_record_endpoint(
    record_id: int,
    payload: RecordUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
    __: None = Depends(limit_requests(bucket="records_write", limit=60, window_seconds=60)),
):
    if payload.record_id != record_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="record_id in body must match the route parameter",
        )
    record = get_record_or_404(db, record_id)
    return update_record(db, record, payload)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record_endpoint(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
    __: None = Depends(limit_requests(bucket="records_write", limit=60, window_seconds=60)),
):
    record = get_record_or_404(db, record_id)
    delete_record(db, record)
    return None
