from sqlalchemy import case, extract, func
from sqlalchemy.orm import Session

from models.record import Record, RecordType


def get_dashboard_summary(db: Session) -> dict:
    income_case = case((Record.type == RecordType.INCOME, Record.amount), else_=0.0)
    expense_case = case((Record.type == RecordType.EXPENSE, Record.amount), else_=0.0)

    income, expenses = db.query(
        func.coalesce(func.sum(income_case), 0.0),
        func.coalesce(func.sum(expense_case), 0.0),
    ).filter(Record.is_deleted.is_(False)).one()

    total_income = float(income or 0.0)
    total_expenses = float(expenses or 0.0)

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_balance": total_income - total_expenses,
    }


def get_category_totals(db: Session, record_type: RecordType | None = None) -> list[dict]:
    query = db.query(
        Record.category.label("category"),
        func.coalesce(func.sum(Record.amount), 0.0).label("total"),
    ).filter(Record.is_deleted.is_(False))
    if record_type:
        query = query.filter(Record.type == record_type)

    rows = (
        query.group_by(Record.category)
        .order_by(func.sum(Record.amount).desc())
        .all()
    )

    return [
        {"category": row.category, "total": float(row.total or 0.0)}
        for row in rows
    ]


def get_recent_activity(db: Session, limit: int = 10) -> list[Record]:
    return (
        db.query(Record)
        .filter(Record.is_deleted.is_(False))
        .order_by(Record.date.desc(), Record.id.desc())
        .limit(limit)
        .all()
    )


def get_monthly_trends(db: Session, year: int | None = None) -> list[dict]:
    year_bucket = extract("year", Record.date).label("year_num")
    month_bucket = extract("month", Record.date).label("month_num")
    income_case = case((Record.type == RecordType.INCOME, Record.amount), else_=0.0)
    expense_case = case((Record.type == RecordType.EXPENSE, Record.amount), else_=0.0)

    query = db.query(
        year_bucket,
        month_bucket,
        func.coalesce(func.sum(income_case), 0.0).label("income"),
        func.coalesce(func.sum(expense_case), 0.0).label("expenses"),
    ).filter(Record.is_deleted.is_(False))
    if year:
        query = query.filter(extract("year", Record.date) == year)

    rows = (
        query.group_by(year_bucket, month_bucket)
        .order_by(year_bucket.asc(), month_bucket.asc())
        .all()
    )

    trends: list[dict] = []
    for row in rows:
        year_num = int(row.year_num)
        month_num = int(row.month_num)
        month_label = f"{year_num:04d}-{month_num:02d}"
        income = float(row.income or 0.0)
        expenses = float(row.expenses or 0.0)
        trends.append(
            {
                "month": month_label,
                "income": income,
                "expenses": expenses,
                "net": income - expenses,
            }
        )
    return trends
