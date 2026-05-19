from sqlmodel import select

from app.models.account_model import Account
from app.models.card_model import Card
from app.models.customer_model import Customer
from app.models.enums import LedgerSide
from app.models.ledger_entry_model import LedgerEntry
from app.models.transaction_model import Transaction
from app.core.dependencies import SessionDep, CurrentUserDep


def _format_entries(rows):
    formatted = []
    for entry, txn in rows:
        signed = entry.amount if entry.entry_type == LedgerSide.CREDIT else -entry.amount
        note = entry.description or (txn.description if txn else None) or (
            txn.transaction_code if txn else None
        )
        formatted.append({
            "entry_id": entry.entry_id,
            "amount": signed,
            "note": note,
            "created_at": entry.created_at,
        })
    return formatted


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

    rows = session.exec(
        select(LedgerEntry, Transaction)
        .join(Transaction, Transaction.transaction_id == LedgerEntry.transaction_id, isouter=True)
        .where(LedgerEntry.account_id == account.account_id)
        .order_by(LedgerEntry.created_at.desc())
    ).all()

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
        "entries": _format_entries(rows),
    }
