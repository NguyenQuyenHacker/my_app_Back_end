from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlmodel import or_, select

from app.models.account_model import Account
from app.models.card_model import Card
from app.models.customer_model import Customer
from app.models.enums import TransactionStatus
from app.models.transaction_model import Transaction
from app.core.dependencies import SessionDep, CurrentUserDep


def get_account_overview_data(session: SessionDep, current_user: CurrentUserDep) -> dict:
    account = session.exec(
        select(Account).where(Account.customer_id == current_user.customer_id)
    ).first()

    if not account:
        return {
            "customer": {"full_name": current_user.full_name},
            "account": None,
            "card": None,
            "entries": [],
        }

    card = session.exec(
        select(Card).where(Card.account_id == account.account_id)
    ).first()

    customer = session.exec(
        select(Customer).where(Customer.customer_id == current_user.customer_id)
    ).first()

    txns = session.exec(
        select(Transaction)
        .where(
            or_(
                Transaction.from_account_id == account.account_id,
                Transaction.to_account_id == account.account_id,
            ),
            Transaction.status.in_([TransactionStatus.SUCCESS, TransactionStatus.PROCESSING, TransactionStatus.PENDING, TransactionStatus.FAILED]),
        )
        .order_by(Transaction.created_at.desc())
    ).all()

    incoming_other_party_ids = {
        t.from_account_id for t in txns
        if t.to_account_id == account.account_id and t.from_account_id is not None
    }
    other_party_accounts = {}
    other_party_customers = {}
    if incoming_other_party_ids:
        rows = session.exec(
            select(Account).where(Account.account_id.in_(incoming_other_party_ids))
        ).all()
        other_party_accounts = {r.account_id: r for r in rows}
        cust_ids = {r.customer_id for r in rows}
        if cust_ids:
            cust_rows = session.exec(
                select(Customer).where(Customer.customer_id.in_(cust_ids))
            ).all()
            other_party_customers = {c.customer_id: c for c in cust_rows}

    items = []
    for txn in txns:
        is_out = txn.from_account_id == account.account_id
        signed_amount = -txn.amount if is_out else txn.amount

        if is_out:
            counterparty_name = txn.to_account_holder or txn.to_bank_account or ""
            counterparty_account = txn.to_bank_account or ""
            counterparty_bank = txn.to_bank_code
        else:
            from_acc = other_party_accounts.get(txn.from_account_id)
            from_cust = other_party_customers.get(from_acc.customer_id) if from_acc else None
            counterparty_name = (from_cust.full_name if from_cust else "") or ""
            counterparty_account = from_acc.account_no if from_acc else ""
            counterparty_bank = from_acc.bank_name if from_acc else None

        sender_full = (customer.full_name if customer else current_user.full_name) or ""
        description = txn.description or (
            f"{sender_full} chuyen tien" if is_out
            else f"{counterparty_name} chuyen"
        )

        items.append({
            "transaction_id": txn.transaction_id,
            "transaction_code": txn.transaction_code,
            "direction": "OUT" if is_out else "IN",
            "transfer_type": txn.transfer_type,
            "status": txn.status,
            "counterparty_name": counterparty_name,
            "counterparty_account": counterparty_account,
            "counterparty_bank_code": counterparty_bank,
            "description": description,
            "amount": signed_amount,
            "currency": txn.currency,
            "created_at": txn.created_at,
            "completed_at": txn.completed_at,
        })

    return {
        "customer": {"full_name": customer.full_name},
        "account": {
            "account_id": account.account_id,
            "account_no": account.account_no,
            "bank_name": account.bank_name,
            "currency": account.currency,
            "balance": account.balance,
            "status": account.status,
        },
        "card": (
            {
                "card_no": card.card_no,
                "status": card.status,
                "expiry_month": card.expiry_month,
                "expiry_year": card.expiry_year,
            }
            if card
            else None
        ),
        "transactions": items,
        "entries": items,
    }


# ============================================================
# Helper: build counterparty info cho 1 transaction
# Dùng chung giữa overview & history endpoint.
# ============================================================
def _build_counterparty(
    txn: Transaction,
    account_id,
    other_party_accounts: dict,
    other_party_customers: dict,
) -> dict:
    is_out = txn.from_account_id == account_id
    if is_out:
        name = txn.to_account_holder or txn.to_bank_account or ""
        acc = txn.to_bank_account or ""
        bank = txn.to_bank_code
    else:
        from_acc = other_party_accounts.get(txn.from_account_id)
        from_cust = (
            other_party_customers.get(from_acc.customer_id) if from_acc else None
        )
        name = (from_cust.full_name if from_cust else "") or ""
        acc = from_acc.account_no if from_acc else ""
        bank = from_acc.bank_name if from_acc else None

    return {
        "is_out": is_out,
        "counterparty_name": name,
        "counterparty_account": acc,
        "counterparty_bank": bank,
    }


# ============================================================
# Service cho Agent tool: tra cứu số dư
# ============================================================
def get_balance_data(session: SessionDep, current_user: CurrentUserDep) -> dict:
    account = session.exec(
        select(Account).where(Account.customer_id == current_user.customer_id)
    ).first()

    if not account:
        return {"has_account": False}

    available = (account.balance or Decimal("0")) - (account.hold_amount or Decimal("0"))

    return {
        "has_account": True,
        "account_no": account.account_no,
        "bank_name": account.bank_name,
        "currency": account.currency,
        "balance": account.balance,
        "hold_amount": account.hold_amount,
        "available_balance": available,
        "status": account.status,
    }


# ============================================================
# Service cho Agent tool: tra cứu lịch sử giao dịch (SUCCESS only)
# ============================================================
def get_transactions_data(
    session: SessionDep,
    current_user: CurrentUserDep,
    limit: int = 5,
    direction: str = "ALL",
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
) -> dict:
    account = session.exec(
        select(Account).where(Account.customer_id == current_user.customer_id)
    ).first()

    filters_echo = {
        "limit": limit,
        "direction": direction,
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
        "min_amount": str(min_amount) if min_amount is not None else None,
        "max_amount": str(max_amount) if max_amount is not None else None,
    }

    if not account:
        return {"filters": filters_echo, "count": 0, "transactions": []}

    stmt = select(Transaction).where(Transaction.status == TransactionStatus.SUCCESS)

    if direction == "IN":
        stmt = stmt.where(Transaction.to_account_id == account.account_id)
    elif direction == "OUT":
        stmt = stmt.where(Transaction.from_account_id == account.account_id)
    else:
        stmt = stmt.where(
            or_(
                Transaction.from_account_id == account.account_id,
                Transaction.to_account_id == account.account_id,
            )
        )

    if date_from:
        stmt = stmt.where(Transaction.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        stmt = stmt.where(Transaction.created_at < datetime.combine(date_to + timedelta(days=1), datetime.min.time()))
    if min_amount is not None:
        stmt = stmt.where(Transaction.amount >= min_amount)
    if max_amount is not None:
        stmt = stmt.where(Transaction.amount <= max_amount)

    txns = session.exec(
        stmt.order_by(Transaction.created_at.desc()).limit(limit)
    ).all()

    incoming_ids = {
        t.from_account_id for t in txns
        if t.to_account_id == account.account_id and t.from_account_id is not None
    }
    other_accs: dict = {}
    other_custs: dict = {}
    if incoming_ids:
        rows = session.exec(
            select(Account).where(Account.account_id.in_(incoming_ids))
        ).all()
        other_accs = {r.account_id: r for r in rows}
        cust_ids = {r.customer_id for r in rows}
        if cust_ids:
            cust_rows = session.exec(
                select(Customer).where(Customer.customer_id.in_(cust_ids))
            ).all()
            other_custs = {c.customer_id: c for c in cust_rows}

    items = []
    for txn in txns:
        cp = _build_counterparty(txn, account.account_id, other_accs, other_custs)
        items.append({
            "transaction_code": txn.transaction_code,
            "direction": "OUT" if cp["is_out"] else "IN",
            "transfer_type": txn.transfer_type,
            "status": txn.status,
            "counterparty_name": cp["counterparty_name"],
            "counterparty_account": cp["counterparty_account"],
            "counterparty_bank": cp["counterparty_bank"],
            "amount": txn.amount,
            "currency": txn.currency,
            "description": txn.description,
            "created_at": txn.created_at,
        })

    return {"filters": filters_echo, "count": len(items), "transactions": items}
