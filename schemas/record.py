from datetime import date as dt_date, datetime

from pydantic import BaseModel, Field

from models.record import RecordType


class RecordBase(BaseModel):
    amount: float = Field(gt=0, description="Amount must be greater than 0")
    type: RecordType
    category: str = Field(min_length=1, max_length=64)
    date: dt_date
    description: str | None = Field(default=None, max_length=500)


class RecordCreate(RecordBase):
    user_id: int = Field(gt=0)


class RecordUpdate(RecordBase):
    record_id: int = Field(gt=0)
    amount: float | None = Field(default=None, gt=0)
    type: RecordType | None = None
    category: str | None = Field(default=None, min_length=1, max_length=64)
    date: dt_date | None = None
    description: str | None = Field(default=None, max_length=500)


class RecordOut(BaseModel):
    id: int
    amount: float
    type: RecordType
    category: str
    date: dt_date
    description: str | None
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
