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
