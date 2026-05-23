import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from app.models.account_model import Account
from app.models.customer_model import Customer
from app.models.enums import (
    AccountStatus,
    LedgerSide,
    SavingsAccountStatus,
    SystemAccountCode,
    TransactionStatus,
    TransferType,
)
from app.models.savings_account_model import SavingsAccount
from app.models.savings_product_model import SavingsProduct
from app.models.system_account_model import SystemAccount
from app.models.transaction_model import Transaction
from app.schemas.client.savings_schema import (
    EarlyWithdrawConfirmResponse,
    EarlyWithdrawInitResponse,
    SavingsAccountOut,
    SavingsConfirmResponse,
    SavingsDetailOut,
    SavingsInitRequest,
    SavingsInitResponse,
    SavingsPreviewRequest,
    SavingsPreviewResponse,
    SavingsProductOut,
)
from app.services.client import (
    idempotency_service,
    ledger_service,
    otp_service,
    transfer_session_service,
)
from app.services.client.transfer_common import (
    ensure_account_active,
    ensure_sufficient_balance,
    generate_transaction_code,
    get_source_account_for_customer,
    lock_account_by_id,
    utcnow,
)

MONEY_Q = Decimal("0.01")


def _q(value: Decimal) -> Decimal:
    return value.quantize(MONEY_Q, rounding=ROUND_HALF_UP)


def _calc_interest_full_term(principal: Decimal, rate: Decimal, term_months: int) -> Decimal:
    interest = principal * rate * Decimal(term_months) / Decimal(12)
    return _q(interest)


def _calc_interest_early(principal: Decimal, early_rate: Decimal, days_held: int) -> Decimal:
    if days_held <= 0:
        return Decimal("0.00")
    interest = principal * early_rate * Decimal(days_held) / Decimal(365)
    return _q(interest)


def _get_product(session: Session, product_id: uuid.UUID, *, must_active: bool = True) -> SavingsProduct:
    product = session.exec(
        select(SavingsProduct).where(SavingsProduct.product_id == product_id)
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Savings product not found")
    if must_active and not product.is_active:
        raise HTTPException(status_code=400, detail="Savings product is not active")
    return product


def _get_system_account(session: Session, code: SystemAccountCode, *, for_update: bool = False) -> Optional[SystemAccount]:
    stmt = select(SystemAccount).where(SystemAccount.account_code == code.value)
    if for_update:
        stmt = stmt.with_for_update()
    return session.exec(stmt).first()


def _require_system_account(session: Session, code: SystemAccountCode, *, for_update: bool = False) -> SystemAccount:
    acc = _get_system_account(session, code, for_update=for_update)
    if not acc:
        raise HTTPException(status_code=500, detail=f"System account {code.value} missing")
    return acc


def _generate_savings_code(session: Session) -> str:
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"TK{today_str}"
    count_stmt = select(func.count()).select_from(SavingsAccount).where(
        SavingsAccount.savings_code.like(f"{prefix}%")
    )
    count = session.exec(count_stmt).one() or 0
    return f"{prefix}{count + 1:03d}"


def _product_label(product: SavingsProduct) -> str:
    return product.name


def _savings_to_out(savings: SavingsAccount, product: Optional[SavingsProduct] = None) -> SavingsAccountOut:
    return SavingsAccountOut(
        savings_id=savings.savings_id,
        savings_code=savings.savings_code,
        product_id=savings.product_id,
        product_name=product.name if product else None,
        product_code=product.code if product else None,
        principal_amount=savings.principal_amount,
        interest_rate=savings.interest_rate,
        term_months=savings.term_months,
        start_date=savings.start_date,
        maturity_date=savings.maturity_date,
        status=savings.status,
        interest_earned=savings.interest_earned,
        final_amount=savings.final_amount,
        closed_at=savings.closed_at,
    )


def list_products(session: Session) -> list[SavingsProductOut]:
    rows = session.exec(
        select(SavingsProduct).where(SavingsProduct.is_active == True).order_by(SavingsProduct.term_months)
    ).all()
    return [SavingsProductOut.model_validate(p, from_attributes=True) for p in rows]


def preview(session: Session, payload: SavingsPreviewRequest) -> SavingsPreviewResponse:
    product = _get_product(session, payload.product_id)
    if payload.amount < product.min_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Amount must be at least {product.min_amount}",
        )
    now = utcnow()
    maturity = now + relativedelta(months=product.term_months)
    interest = _calc_interest_full_term(payload.amount, product.interest_rate, product.term_months)
    return SavingsPreviewResponse(
        product_id=product.product_id,
        product_name=product.name,
        term_months=product.term_months,
        interest_rate=product.interest_rate,
        principal=_q(payload.amount),
        interest_earned=interest,
        final_amount=_q(payload.amount + interest),
        start_date=now,
        maturity_date=maturity,
    )


def init_deposit(
    session: Session,
    *,
    current_user: Customer,
    payload: SavingsInitRequest,
    idempotency_key: Optional[str],
) -> SavingsInitResponse:
    if idempotency_key:
        cached = idempotency_service.get_existing(session, idempotency_key, current_user.customer_id)
        if cached:
            return SavingsInitResponse(**cached)

    source = get_source_account_for_customer(session, current_user.customer_id)
    ensure_account_active(source, "Source")

    product = _get_product(session, payload.product_id)
    if payload.amount < product.min_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Amount must be at least {product.min_amount}",
        )
    ensure_sufficient_balance(source, payload.amount)

    now = utcnow()
    maturity = now + relativedelta(months=product.term_months)
    expected_interest = _calc_interest_full_term(payload.amount, product.interest_rate, product.term_months)

    sess = transfer_session_service.create_session(
        session,
        customer_id=current_user.customer_id,
        source_account_id=source.account_id,
        transfer_type=TransferType.SAVINGS_DEPOSIT,
        payload={
            "product_id": str(product.product_id),
            "amount": str(_q(payload.amount)),
        },
    )

    response = SavingsInitResponse(
        session_id=sess.session_id,
        product_id=product.product_id,
        product_name=product.name,
        term_months=product.term_months,
        interest_rate=product.interest_rate,
        principal=_q(payload.amount),
        expected_interest=expected_interest,
        expected_final_amount=_q(payload.amount + expected_interest),
        expected_maturity_date=maturity,
        expires_at=sess.expires_at,
    )

    if idempotency_key:
        idempotency_service.save(
            session,
            key=idempotency_key,
            user_id=current_user.customer_id,
            status_code=200,
            response_body=response.model_dump(mode="json"),
        )
    session.commit()
    return response


def confirm_deposit(
    session: Session,
    *,
    current_user: Customer,
    session_id: uuid.UUID,
    otp: str,
    idempotency_key: Optional[str],
) -> SavingsConfirmResponse:
    if idempotency_key:
        cached = idempotency_service.get_existing(session, idempotency_key, current_user.customer_id)
        if cached:
            return SavingsConfirmResponse(**cached)

    sess = transfer_session_service.load_active_session(
        session,
        session_id=session_id,
        customer_id=current_user.customer_id,
        transfer_type=TransferType.SAVINGS_DEPOSIT,
    )
    if not sess:
        raise HTTPException(status_code=400, detail="Invalid or expired savings session")

    body = sess.payload
    product_id = uuid.UUID(body["product_id"])
    amount = Decimal(body["amount"])

    product = _get_product(session, product_id)

    source = lock_account_by_id(session, sess.source_account_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source account not found")
    ensure_account_active(source, "Source")

    if not otp_service.verify_otp(otp, source.otp_hash):
        raise HTTPException(status_code=401, detail="Invalid OTP")

    ensure_sufficient_balance(source, amount)

    pool = _require_system_account(session, SystemAccountCode.SAVINGS_POOL, for_update=True)

    now = utcnow()
    maturity = now + relativedelta(months=product.term_months)

    savings = SavingsAccount(
        savings_code=_generate_savings_code(session),
        customer_id=current_user.customer_id,
        account_id=source.account_id,
        product_id=product.product_id,
        principal_amount=amount,
        interest_rate=product.interest_rate,
        early_withdrawal_rate=product.early_withdrawal_rate,
        term_months=product.term_months,
        start_date=now,
        maturity_date=maturity,
        status=SavingsAccountStatus.ACTIVE,
        interest_earned=Decimal("0.00"),
        final_amount=Decimal("0.00"),
        created_at=now,
        updated_at=now,
    )
    session.add(savings)
    session.flush()

    txn = Transaction(
        transaction_code=generate_transaction_code(session),
        idempotency_key=idempotency_key,
        transfer_type=TransferType.SAVINGS_DEPOSIT,
        status=TransactionStatus.SUCCESS,
        from_account_id=source.account_id,
        from_customer_id=current_user.customer_id,
        to_account_id=None,
        to_customer_id=None,
        to_bank_code=None,
        to_bank_account=savings.savings_code,
        to_account_holder=current_user.full_name,
        amount=amount,
        currency=source.currency or "VND",
        description=f"Gửi tiết kiệm {product.name}",
        created_at=now,
        updated_at=now,
        completed_at=now,
    )
    session.add(txn)
    session.flush()

    source.balance -= amount
    source.updated_at = now
    pool.balance += amount
    pool.updated_at = now

    ledger_service.post_double_entry(
        session,
        transaction_id=txn.transaction_id,
        amount=amount,
        debit={"account_id": source.account_id, "balance_after": source.balance},
        credit={"system_account_id": pool.id, "balance_after": pool.balance},
        description=f"Gửi tiết kiệm {savings.savings_code}",
        currency=source.currency or "VND",
    )

    transfer_session_service.consume(sess)

    response = SavingsConfirmResponse(
        transaction_id=txn.transaction_id,
        transaction_code=txn.transaction_code,
        savings=_savings_to_out(savings, product),
        new_balance=source.balance,
        created_at=txn.created_at,
    )

    if idempotency_key:
        idempotency_service.save(
            session,
            key=idempotency_key,
            user_id=current_user.customer_id,
            status_code=200,
            response_body=response.model_dump(mode="json"),
        )
    session.commit()
    return response


def list_my_accounts(
    session: Session,
    *,
    current_user: Customer,
    status: Optional[SavingsAccountStatus] = None,
) -> list[SavingsAccountOut]:
    stmt = select(SavingsAccount).where(SavingsAccount.customer_id == current_user.customer_id)
    if status is not None:
        stmt = stmt.where(SavingsAccount.status == status)
    stmt = stmt.order_by(SavingsAccount.created_at.desc())
    rows = session.exec(stmt).all()
    if not rows:
        return []
    product_ids = {r.product_id for r in rows}
    products = session.exec(select(SavingsProduct).where(SavingsProduct.product_id.in_(product_ids))).all()
    by_id = {p.product_id: p for p in products}
    return [_savings_to_out(r, by_id.get(r.product_id)) for r in rows]


def get_detail(session: Session, *, current_user: Customer, savings_id: uuid.UUID) -> SavingsDetailOut:
    row = session.exec(
        select(SavingsAccount).where(SavingsAccount.savings_id == savings_id)
    ).first()
    if not row or row.customer_id != current_user.customer_id:
        raise HTTPException(status_code=404, detail="Savings account not found")
    product = session.exec(
        select(SavingsProduct).where(SavingsProduct.product_id == row.product_id)
    ).first()

    projected_interest = _calc_interest_full_term(row.principal_amount, row.interest_rate, row.term_months)

    now = utcnow()
    start = row.start_date
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    days_held = max(0, (now - start).days)

    base = _savings_to_out(row, product).model_dump()
    return SavingsDetailOut(
        **base,
        projected_interest_at_maturity=projected_interest,
        projected_final_amount_at_maturity=_q(row.principal_amount + projected_interest),
        days_held=days_held,
    )


def _load_user_savings_for_update(
    session: Session, *, customer_id: uuid.UUID, savings_id: uuid.UUID
) -> SavingsAccount:
    row = session.exec(
        select(SavingsAccount).where(SavingsAccount.savings_id == savings_id).with_for_update()
    ).first()
    if not row or row.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Savings account not found")
    return row


def init_early_withdraw(
    session: Session,
    *,
    current_user: Customer,
    savings_id: uuid.UUID,
    idempotency_key: Optional[str],
) -> EarlyWithdrawInitResponse:
    if idempotency_key:
        cached = idempotency_service.get_existing(session, idempotency_key, current_user.customer_id)
        if cached:
            return EarlyWithdrawInitResponse(**cached)

    row = session.exec(
        select(SavingsAccount).where(SavingsAccount.savings_id == savings_id)
    ).first()
    if not row or row.customer_id != current_user.customer_id:
        raise HTTPException(status_code=404, detail="Savings account not found")
    if row.status != SavingsAccountStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Savings account is not ACTIVE")

    now = utcnow()
    start = row.start_date if row.start_date.tzinfo else row.start_date.replace(tzinfo=timezone.utc)
    days_held = max(0, (now - start).days)
    est_interest = _calc_interest_early(row.principal_amount, row.early_withdrawal_rate, days_held)

    sess = transfer_session_service.create_session(
        session,
        customer_id=current_user.customer_id,
        source_account_id=row.account_id,
        transfer_type=TransferType.SAVINGS_EARLY_WITHDRAWAL,
        payload={"savings_id": str(row.savings_id)},
    )

    response = EarlyWithdrawInitResponse(
        session_id=sess.session_id,
        savings_id=row.savings_id,
        principal=row.principal_amount,
        days_held=days_held,
        estimated_interest=est_interest,
        estimated_final_amount=_q(row.principal_amount + est_interest),
        expires_at=sess.expires_at,
    )

    if idempotency_key:
        idempotency_service.save(
            session,
            key=idempotency_key,
            user_id=current_user.customer_id,
            status_code=200,
            response_body=response.model_dump(mode="json"),
        )
    session.commit()
    return response


def confirm_early_withdraw(
    session: Session,
    *,
    current_user: Customer,
    session_id: uuid.UUID,
    otp: str,
    idempotency_key: Optional[str],
) -> EarlyWithdrawConfirmResponse:
    if idempotency_key:
        cached = idempotency_service.get_existing(session, idempotency_key, current_user.customer_id)
        if cached:
            return EarlyWithdrawConfirmResponse(**cached)

    sess = transfer_session_service.load_active_session(
        session,
        session_id=session_id,
        customer_id=current_user.customer_id,
        transfer_type=TransferType.SAVINGS_EARLY_WITHDRAWAL,
    )
    if not sess:
        raise HTTPException(status_code=400, detail="Invalid or expired savings session")

    savings_id = uuid.UUID(sess.payload["savings_id"])
    savings = _load_user_savings_for_update(session, customer_id=current_user.customer_id, savings_id=savings_id)
    if savings.status != SavingsAccountStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Savings account is not ACTIVE")

    account = lock_account_by_id(session, savings.account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.status not in (AccountStatus.ACTIVE,):
        raise HTTPException(status_code=400, detail="Account is not ACTIVE")

    if not otp_service.verify_otp(otp, account.otp_hash):
        raise HTTPException(status_code=401, detail="Invalid OTP")

    pool = _require_system_account(session, SystemAccountCode.SAVINGS_POOL, for_update=True)
    interest_expense = _get_system_account(session, SystemAccountCode.INTEREST_EXPENSE, for_update=True)

    now = utcnow()
    start = savings.start_date if savings.start_date.tzinfo else savings.start_date.replace(tzinfo=timezone.utc)
    days_held = max(0, (now - start).days)
    interest = _calc_interest_early(savings.principal_amount, savings.early_withdrawal_rate, days_held)
    final_amount = _q(savings.principal_amount + interest)

    product = session.exec(select(SavingsProduct).where(SavingsProduct.product_id == savings.product_id)).first()

    txn = Transaction(
        transaction_code=generate_transaction_code(session),
        idempotency_key=idempotency_key,
        transfer_type=TransferType.SAVINGS_EARLY_WITHDRAWAL,
        status=TransactionStatus.SUCCESS,
        from_account_id=None,
        from_customer_id=None,
        to_account_id=account.account_id,
        to_customer_id=current_user.customer_id,
        to_bank_code=None,
        to_bank_account=account.account_no,
        to_account_holder=current_user.full_name,
        amount=final_amount,
        currency=account.currency or "VND",
        description=f"Tất toán sớm {savings.savings_code}",
        created_at=now,
        updated_at=now,
        completed_at=now,
    )
    session.add(txn)
    session.flush()

    account.balance += final_amount
    account.updated_at = now
    pool.balance -= savings.principal_amount
    pool.updated_at = now

    ledger_service.post_double_entry(
        session,
        transaction_id=txn.transaction_id,
        amount=savings.principal_amount,
        debit={"system_account_id": pool.id, "balance_after": pool.balance},
        credit={"account_id": account.account_id, "balance_after": account.balance - interest},
        description=f"Rút gốc tiết kiệm {savings.savings_code}",
        currency=account.currency or "VND",
    )

    if interest > 0:
        if interest_expense is not None:
            interest_expense.balance += interest
            interest_expense.updated_at = now
            interest_credit_target = {"account_id": account.account_id, "balance_after": account.balance}
            interest_debit_target = {"system_account_id": interest_expense.id, "balance_after": interest_expense.balance}
        else:
            pool.balance -= interest
            pool.updated_at = now
            interest_credit_target = {"account_id": account.account_id, "balance_after": account.balance}
            interest_debit_target = {"system_account_id": pool.id, "balance_after": pool.balance}

        ledger_service.post_double_entry(
            session,
            transaction_id=txn.transaction_id,
            amount=interest,
            debit=interest_debit_target,
            credit=interest_credit_target,
            description="Lãi tất toán sớm",
            currency=account.currency or "VND",
        )

    savings.status = SavingsAccountStatus.WITHDRAWN_EARLY
    savings.interest_earned = interest
    savings.final_amount = final_amount
    savings.closed_at = now
    savings.updated_at = now

    transfer_session_service.consume(sess)

    response = EarlyWithdrawConfirmResponse(
        transaction_id=txn.transaction_id,
        transaction_code=txn.transaction_code,
        savings=_savings_to_out(savings, product),
        new_balance=account.balance,
        created_at=txn.created_at,
    )

    if idempotency_key:
        idempotency_service.save(
            session,
            key=idempotency_key,
            user_id=current_user.customer_id,
            status_code=200,
            response_body=response.model_dump(mode="json"),
        )
    session.commit()
    return response


def process_maturity_for_account(session: Session, savings_id: uuid.UUID) -> bool:
    savings = session.exec(
        select(SavingsAccount).where(SavingsAccount.savings_id == savings_id).with_for_update()
    ).first()
    if savings is None:
        return False
    if savings.status != SavingsAccountStatus.ACTIVE:
        return False

    now = utcnow()
    maturity = savings.maturity_date if savings.maturity_date.tzinfo else savings.maturity_date.replace(tzinfo=timezone.utc)
    if maturity > now:
        return False

    account = lock_account_by_id(session, savings.account_id)
    if account is None:
        return False

    pool = _require_system_account(session, SystemAccountCode.SAVINGS_POOL, for_update=True)

    interest = _calc_interest_full_term(savings.principal_amount, savings.interest_rate, savings.term_months)
    final_amount = _q(savings.principal_amount + interest)

    txn = Transaction(
        transaction_code=generate_transaction_code(session),
        idempotency_key=None,
        transfer_type=TransferType.SAVINGS_MATURITY,
        status=TransactionStatus.SUCCESS,
        from_account_id=None,
        from_customer_id=None,
        to_account_id=account.account_id,
        to_customer_id=savings.customer_id,
        to_bank_code=None,
        to_bank_account=account.account_no,
        to_account_holder="",
        amount=final_amount,
        currency=account.currency or "VND",
        description=f"Đáo hạn tiết kiệm {savings.savings_code}",
        created_at=now,
        updated_at=now,
        completed_at=now,
    )
    session.add(txn)
    session.flush()

    account.balance += final_amount
    account.updated_at = now
    pool.balance -= final_amount
    pool.updated_at = now

    ledger_service.post_double_entry(
        session,
        transaction_id=txn.transaction_id,
        amount=final_amount,
        debit={"system_account_id": pool.id, "balance_after": pool.balance},
        credit={"account_id": account.account_id, "balance_after": account.balance},
        description=f"Đáo hạn {savings.savings_code} (gốc+lãi)",
        currency=account.currency or "VND",
    )

    savings.status = SavingsAccountStatus.MATURED
    savings.interest_earned = interest
    savings.final_amount = final_amount
    savings.closed_at = now
    savings.updated_at = now

    return True
