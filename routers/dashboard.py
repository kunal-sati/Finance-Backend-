from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import require_roles
from models.record import RecordType
from models.user import User, UserRole
from schemas.dashboard import CategoryTotal, DashboardSummary, MonthlyTrend, RecentActivity
from services.dashboard_service import (
    get_category_totals,
    get_dashboard_summary,
    get_monthly_trends,
    get_recent_activity,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN)),
):
    return get_dashboard_summary(db)


@router.get("/category-totals", response_model=list[CategoryTotal])
def category_totals(
    record_type: RecordType | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN)),
):
    return get_category_totals(db, record_type=record_type)


@router.get("/recent-activity", response_model=list[RecentActivity])
def recent_activity(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN)),
):
    return get_recent_activity(db, limit=limit)


@router.get("/monthly-trends", response_model=list[MonthlyTrend])
def monthly_trends(
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN)),
):
    return get_monthly_trends(db, year=year)