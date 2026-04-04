from datetime import date

from pydantic import BaseModel

from models.record import RecordType


class DashboardSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float


class CategoryTotal(BaseModel):
    category: str
    total: float


class MonthlyTrend(BaseModel):
    month: str
    income: float
    expenses: float
    net: float


class RecentActivity(BaseModel):
    id: int
    amount: float
    type: RecordType
    category: str
    date: date
    description: str | None
