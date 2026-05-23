import uuid
from calendar import monthrange
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from sqlalchemy import case, func
from sqlmodel import Session, select

from app.models.customer_model import Customer
from app.models.enums import TransactionStatus, TransferType
from app.models.transaction_model import Transaction
from app.schemas.client.statistics_schema import (
    DailyOut,
    DailyPoint,
    ExpenseByTypeItem,
    ExpenseByTypeOut,
    OverviewOut,
    TopRecipientItem,
    TopRecipientsOut,
    TrendOut,
    TrendPoint,
)
from app.services.client.transfer_common import get_source_account_for_customer

TRANSFER_TYPE_LABEL = {
    TransferType.INTERNAL.value: "Chuyển nội bộ",
    TransferType.EXTERNAL.value: "Chuyển liên ngân hàng",
    TransferType.SAVINGS_DEPOSIT.value: "Gửi tiết kiệm",
    TransferType.SAVINGS_MATURITY.value: "Đáo hạn tiết kiệm",
    TransferType.SAVINGS_EARLY_WITHDRAWAL.value: "Tất toán sớm",
}


def _parse_month(month: Optional[str]) -> date:
    if not month:
        today = datetime.now(timezone.utc).date()
        return today.replace(day=1)
    try:
        y, m = month.split("-")
        return date(int(y), int(m), 1)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid month format, expected YYYY-MM")


def _month_range(month_start: date) -> tuple[datetime, datetime]:
    start = datetime(month_start.year, month_start.month, 1, tzinfo=timezone.utc)
    end = start + relativedelta(months=1)
    return start, end


def _format_period(month_start: date) -> str:
    return f"{month_start.year:04d}-{month_start.month:02d}"


def _pct_change(current: Decimal, previous: Decimal) -> Optional[Decimal]:
    if previous == 0:
        return None
    diff = (current - previous) / previous * Decimal(100)
    return diff.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _get_account_id(session: Session, current_user: Customer) -> uuid.UUID:
    return get_source_account_for_customer(session, current_user.customer_id).account_id


def _sum_in_range(session: Session, account_id: uuid.UUID, start: datetime, end: datetime, *, direction: str) -> tuple[Decimal, int]:
    column = Transaction.to_account_id if direction == "income" else Transaction.from_account_id
    stmt = select(
        func.coalesce(func.sum(Transaction.amount), 0),
        func.count(),
    ).where(
        column == account_id,
        Transaction.status == TransactionStatus.SUCCESS,
        Transaction.created_at >= start,
        Transaction.created_at < end,
    )
    total, count = session.exec(stmt).one()
    return Decimal(total or 0), int(count or 0)


def overview(session: Session, *, current_user: Customer, month: Optional[str]) -> OverviewOut:
    account_id = _get_account_id(session, current_user)
    month_start = _parse_month(month)
    cur_start, cur_end = _month_range(month_start)
    prev_start, prev_end = _month_range(month_start - relativedelta(months=1))

    cur_income, income_count = _sum_in_range(session, account_id, cur_start, cur_end, direction="income")
    cur_expense, expense_count = _sum_in_range(session, account_id, cur_start, cur_end, direction="expense")
    prev_income, _ = _sum_in_range(session, account_id, prev_start, prev_end, direction="income")
    prev_expense, _ = _sum_in_range(session, account_id, prev_start, prev_end, direction="expense")

    return OverviewOut(
        period=_format_period(month_start),
        total_income=cur_income,
        total_expense=cur_expense,
        net=cur_income - cur_expense,
        transaction_count=income_count + expense_count,
        income_change_percent=_pct_change(cur_income, prev_income),
        expense_change_percent=_pct_change(cur_expense, prev_expense),
    )


def expense_by_type(session: Session, *, current_user: Customer, month: Optional[str]) -> ExpenseByTypeOut:
    account_id = _get_account_id(session, current_user)
    month_start = _parse_month(month)
    start, end = _month_range(month_start)

    stmt = select(
        Transaction.transfer_type,
        func.coalesce(func.sum(Transaction.amount), 0),
        func.count(),
    ).where(
        Transaction.from_account_id == account_id,
        Transaction.status == TransactionStatus.SUCCESS,
        Transaction.created_at >= start,
        Transaction.created_at < end,
    ).group_by(Transaction.transfer_type)

    rows = session.exec(stmt).all()
    items = []
    total = Decimal(0)
    for transfer_type, amount, count in rows:
        type_value = transfer_type.value if hasattr(transfer_type, "value") else str(transfer_type)
        amt = Decimal(amount or 0)
        total += amt
        items.append(ExpenseByTypeItem(
            transfer_type=type_value,
            label=TRANSFER_TYPE_LABEL.get(type_value, type_value),
            total=amt,
            count=int(count or 0),
        ))
    items.sort(key=lambda x: x.total, reverse=True)
    return ExpenseByTypeOut(period=_format_period(month_start), total_expense=total, items=items)


def daily(session: Session, *, current_user: Customer, month: Optional[str]) -> DailyOut:
    account_id = _get_account_id(session, current_user)
    month_start = _parse_month(month)
    start, end = _month_range(month_start)

    expense_sum = func.sum(case((Transaction.from_account_id == account_id, Transaction.amount), else_=0))
    income_sum = func.sum(case((Transaction.to_account_id == account_id, Transaction.amount), else_=0))

    stmt = select(
        func.date(Transaction.created_at).label("day"),
        income_sum.label("income"),
        expense_sum.label("expense"),
    ).where(
        ((Transaction.from_account_id == account_id) | (Transaction.to_account_id == account_id)),
        Transaction.status == TransactionStatus.SUCCESS,
        Transaction.created_at >= start,
        Transaction.created_at < end,
    ).group_by(func.date(Transaction.created_at)).order_by(func.date(Transaction.created_at))

    rows = session.exec(stmt).all()
    by_day = {row[0]: (Decimal(row[1] or 0), Decimal(row[2] or 0)) for row in rows}

    days_in_month = monthrange(month_start.year, month_start.month)[1]
    points = []
    for d in range(1, days_in_month + 1):
        day_obj = date(month_start.year, month_start.month, d)
        inc, exp = by_day.get(day_obj, (Decimal(0), Decimal(0)))
        points.append(DailyPoint(day=day_obj.isoformat(), income=inc, expense=exp))

    return DailyOut(period=_format_period(month_start), points=points)


def top_recipients(session: Session, *, current_user: Customer, month: Optional[str], limit: int) -> TopRecipientsOut:
    account_id = _get_account_id(session, current_user)
    month_start = _parse_month(month)
    start, end = _month_range(month_start)

    internal_stmt = select(
        Transaction.to_customer_id,
        Transaction.to_account_holder,
        Transaction.to_bank_account,
        func.sum(Transaction.amount),
        func.count(),
    ).where(
        Transaction.from_account_id == account_id,
        Transaction.transfer_type == TransferType.INTERNAL,
        Transaction.status == TransactionStatus.SUCCESS,
        Transaction.created_at >= start,
        Transaction.created_at < end,
        Transaction.to_customer_id.is_not(None),
    ).group_by(Transaction.to_customer_id, Transaction.to_account_holder, Transaction.to_bank_account)

    external_stmt = select(
        Transaction.to_bank_account,
        Transaction.to_bank_code,
        Transaction.to_account_holder,
        func.sum(Transaction.amount),
        func.count(),
    ).where(
        Transaction.from_account_id == account_id,
        Transaction.transfer_type == TransferType.EXTERNAL,
        Transaction.status == TransactionStatus.SUCCESS,
        Transaction.created_at >= start,
        Transaction.created_at < end,
    ).group_by(Transaction.to_bank_account, Transaction.to_bank_code, Transaction.to_account_holder)

    items: list[TopRecipientItem] = []

    for cust_id, holder, acc_no, amount, count in session.exec(internal_stmt).all():
        items.append(TopRecipientItem(
            name=holder or "",
            account_no=acc_no,
            bank_code=None,
            customer_id=cust_id,
            is_internal=True,
            total=Decimal(amount or 0),
            count=int(count or 0),
        ))

    for acc_no, bank_code, holder, amount, count in session.exec(external_stmt).all():
        items.append(TopRecipientItem(
            name=holder or "",
            account_no=acc_no,
            bank_code=bank_code,
            customer_id=None,
            is_internal=False,
            total=Decimal(amount or 0),
            count=int(count or 0),
        ))

    items.sort(key=lambda x: x.total, reverse=True)
    return TopRecipientsOut(period=_format_period(month_start), items=items[:limit])


def trend(session: Session, *, current_user: Customer, months: int) -> TrendOut:
    if months <= 0 or months > 24:
        raise HTTPException(status_code=400, detail="months must be between 1 and 24")
    account_id = _get_account_id(session, current_user)

    today = datetime.now(timezone.utc).date().replace(day=1)
    points = []
    for i in range(months - 1, -1, -1):
        month_start = today - relativedelta(months=i)
        start, end = _month_range(month_start)
        income, _ = _sum_in_range(session, account_id, start, end, direction="income")
        expense, _ = _sum_in_range(session, account_id, start, end, direction="expense")
        points.append(TrendPoint(
            period=_format_period(month_start),
            total_income=income,
            total_expense=expense,
        ))
    return TrendOut(months=months, points=points)
