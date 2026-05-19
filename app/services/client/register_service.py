import secrets
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core.security import create_access_token, hash_password
from app.models.account_model import Account
from app.models.card_model import Card
from app.models.customer_model import Customer
from app.models.enums import AccountStatus, CardStatus
from app.models.user_model import User
from app.schemas.client.register_schema import (
    RegisteredAccount,
    RegisteredCard,
    RegisterRequest,
    RegisterResponse,
)

# NOTE: DB has trigger validate_card_no_matches_account_no() requiring
# cards.card_no == accounts.account_no. So we generate ONE number and reuse it.
ACCOUNT_NO_PREFIX = "1903"   # 4 digits → final length = 12
DEFAULT_CURRENCY = "VND"
CARD_VALIDITY_YEARS = 5


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _check_unique_fields(session: Session, data: RegisterRequest) -> None:
    if session.exec(select(Customer).where(Customer.phone == data.phone)).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="PHONE_ALREADY_REGISTERED",
        )

    if session.exec(select(Customer).where(Customer.cccd_number == data.cccd_number)).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CCCD_ALREADY_REGISTERED",
        )

    if data.email:
        if session.exec(select(Customer).where(Customer.email == data.email)).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="EMAIL_ALREADY_REGISTERED",
            )


def _generate_unique_account_no(session: Session) -> str:
    """Generate a number unique across BOTH accounts.account_no and cards.card_no
    (DB trigger requires they match)."""
    for _ in range(10):
        suffix = "".join(str(secrets.randbelow(10)) for _ in range(8))
        candidate = f"{ACCOUNT_NO_PREFIX}{suffix}"
        account_exists = session.exec(
            select(Account).where(Account.account_no == candidate)
        ).first()
        card_exists = session.exec(
            select(Card).where(Card.card_no == candidate)
        ).first()
        if not account_exists and not card_exists:
            return candidate
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Không thể sinh số tài khoản, thử lại sau",
    )


def _mask_card_no(card_no: str) -> str:
    if len(card_no) < 8:
        return card_no
    if len(card_no) >= 16:
        return f"{card_no[:4]} **** **** {card_no[-4:]}"
    return f"{card_no[:4]} **** {card_no[-4:]}"


def register_customer(session: Session, data: RegisterRequest) -> RegisterResponse:
    _check_unique_fields(session, data)

    now = _utcnow()

    # 1. Customer
    customer = Customer(
        full_name=data.full_name.strip(),
        cccd_number=data.cccd_number,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        permanent_address=data.permanent_address.strip(),
        current_address=data.current_address.strip(),
        occupation=data.occupation.strip(),
        email=data.email,
        phone=data.phone,
        identity_issue_date=data.identity_issue_date,
        identity_expiry_date=data.identity_expiry_date,
        identity_issue_place=(data.identity_issue_place or "").strip() or None,
        created_at=now,
        updated_at=now,
    )
    session.add(customer)
    session.flush()

    # 2. User (login credentials)
    user = User(
        customer_id=customer.customer_id,
        password_hash=hash_password(data.password),
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(user)

    # 3. Account (payment account, opening balance = 0, PIN = user-supplied)
    account_no = _generate_unique_account_no(session)
    pin_hash = hash_password(data.pin)
    account = Account(
        customer_id=customer.customer_id,
        account_no=account_no,
        bank_name="TCB",
        status=AccountStatus.ACTIVE,
        currency=DEFAULT_CURRENCY,
        balance=Decimal("0.00"),
        otp_hash=pin_hash,
        opened_at=now,
        created_at=now,
        updated_at=now,
    )
    session.add(account)
    session.flush()

    # 4. Card (debit card linked to the account)
    # DB constraint: card_no must equal account_no
    expiry_year = now.year + CARD_VALIDITY_YEARS
    card = Card(
        account_id=account.account_id,
        card_no=account_no,
        status=CardStatus.ACTIVE,
        issued_at=now,
        expiry_month=now.month,
        expiry_year=expiry_year,
        created_at=now,
        updated_at=now,
    )
    session.add(card)

    session.commit()
    session.refresh(customer)
    session.refresh(account)
    session.refresh(card)

    access_token = create_access_token({
        "sub": str(customer.customer_id),
        "role": "client",
    })

    return RegisterResponse(
        customer_id=str(customer.customer_id),
        full_name=customer.full_name,
        phone=customer.phone,
        email=customer.email,
        access_token=access_token,
        account=RegisteredAccount(
            account_id=str(account.account_id),
            account_no=account.account_no,
            bank_name=account.bank_name,
            currency=account.currency,
            balance=str(account.balance),
            status=account.status.value,
        ),
        card=RegisteredCard(
            card_id=str(card.card_id),
            card_no_masked=_mask_card_no(card.card_no),
            status=card.status.value,
            expiry_month=card.expiry_month,
            expiry_year=card.expiry_year,
        ),
    )
