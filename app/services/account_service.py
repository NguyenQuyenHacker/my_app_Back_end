#
from sqlmodel import select

from app.models.account_model import Account
from app.models.card_model import Card
from app.models.customer_model import Customer
from app.models.ledger_model import Entry
from app.core.dependencies import SessionDep, CurrentUserDep

def get_account_overview_data(session: SessionDep, current_user: CurrentUserDep) -> dict:
    account = session.exec(
        select(Account).where(Account.customer_id == current_user.customer_id)
    ).first()

    if not account:
        return {    
            "customer": {
                "full_name": current_user.full_name,
            },
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
    
    entries = session.exec(
        select(Entry)
        .where(Entry.account_id == account.account_id)
        .order_by(Entry.created_at.desc())
    ).all()

    return {
        "customer": {
            "full_name": customer.full_name,
        },
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
        "entries": [
            {
                "entry_id": e.entry_id,
                "amount": e.amount,
                "note": e.note,
                "created_at": e.created_at,
            }
            for e in entries
        ],
    }