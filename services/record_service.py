from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from models.record import Record, RecordType
from models.user import User
from schemas.record import RecordCreate, RecordUpdate


def create_record(db: Session, payload: RecordCreate, user_id: int) -> Record:
    owner = db.query(User.id).filter(User.id == user_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner user not found for provided user_id",
        )
    record = Record(
        amount=payload.amount,
        type=payload.type,
        category=payload.category,
        date=payload.date,
        description=payload.description,
        user_id=user_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_records(
    db: Session,
    record_type: RecordType | None = None,
    category: str | None = None,
    search: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Record]:
    query = db.query(Record).filter(Record.is_deleted.is_(False))

    if record_type:
        query = query.filter(Record.type == record_type)
    if category:
        query = query.filter(func.lower(Record.category) == category.strip().lower())
    if search:
        search_value = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Record.category.ilike(search_value),
                Record.description.ilike(search_value),
            )
        )
    if start_date:
        query = query.filter(Record.date >= start_date)
    if end_date:
        query = query.filter(Record.date <= end_date)

    return (
        query.order_by(Record.date.desc(), Record.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_record_or_404(db: Session, record_id: int) -> Record:
    record = (
        db.query(Record)
        .filter(Record.id == record_id, Record.is_deleted.is_(False))
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )
    return record


def update_record(db: Session, record: Record, payload: RecordUpdate) -> Record:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update fields provided",
        )
    new_user_id = updates.get("user_id")
    if new_user_id is not None:
        owner = db.query(User.id).filter(User.id == new_user_id).first()
        if not owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Owner user not found for provided user_id",
            )


    for field, value in updates.items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


def delete_record(db: Session, record: Record) -> None:
    record.is_deleted = True
    record.deleted_at = func.now()
    db.commit()