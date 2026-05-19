import asyncio
import logging

from sqlmodel import Session, select

from app.db.database import engine
from app.models.enums import TransactionStatus, TransferType
from app.models.transaction_model import Transaction
from app.services.client import napas_mock
from app.services.client.transfer_external_service import (
    _settle_failure,
    _settle_success,
)

logger = logging.getLogger(__name__)

RECONCILE_INTERVAL_SECONDS = 5 * 60


def _reconcile_once() -> int:
    processed = 0
    with Session(engine) as session:
        rows = session.exec(
            select(Transaction).where(
                Transaction.status == TransactionStatus.PROCESSING,
                Transaction.transfer_type == TransferType.EXTERNAL,
            )
        ).all()
        for txn in rows:
            try:
                result = napas_mock.send_to_napas(
                    bank_code=txn.to_bank_code,
                    account_number=txn.to_bank_account,
                    amount=txn.amount,
                    description=txn.description,
                    simulate_delay=False,
                )
                if result["status"] == "SUCCESS":
                    _settle_success(session, txn, result["ref_id"])
                    session.commit()
                    processed += 1
                elif result["status"] == "FAILED":
                    _settle_failure(session, txn, result["ref_id"], result.get("reason") or "UNKNOWN")
                    session.commit()
                    processed += 1
            except Exception as exc:
                session.rollback()
                logger.exception("Failed reconciling txn %s: %s", txn.transaction_id, exc)
    return processed


async def reconcile_loop() -> None:
    while True:
        try:
            count = await asyncio.to_thread(_reconcile_once)
            if count:
                logger.info("Reconciled %d processing transactions", count)
        except Exception:
            logger.exception("Reconcile job iteration crashed")
        await asyncio.sleep(RECONCILE_INTERVAL_SECONDS)
