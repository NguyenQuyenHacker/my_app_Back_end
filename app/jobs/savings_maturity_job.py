import asyncio
import logging
from datetime import datetime, time, timedelta, timezone

from sqlmodel import Session, select

from app.db.database import engine
from app.models.enums import SavingsAccountStatus
from app.models.savings_account_model import SavingsAccount
from app.services.client import savings_service

logger = logging.getLogger(__name__)


def _run_once() -> int:
    processed = 0
    with Session(engine) as session:
        ids = session.exec(
            select(SavingsAccount.savings_id).where(
                SavingsAccount.status == SavingsAccountStatus.ACTIVE,
                SavingsAccount.maturity_date <= datetime.now(timezone.utc),
            )
        ).all()
        for sid in ids:
            try:
                ok = savings_service.process_maturity_for_account(session, sid)
                if ok:
                    session.commit()
                    processed += 1
                else:
                    session.rollback()
            except Exception as exc:
                session.rollback()
                logger.exception("Failed processing savings maturity %s: %s", sid, exc)
    return processed


def _seconds_until_next_run() -> float:
    now = datetime.now(timezone.utc)
    next_run = datetime.combine(now.date(), time(0, 5, tzinfo=timezone.utc))
    if next_run <= now:
        next_run = next_run + timedelta(days=1)
    return max(60.0, (next_run - now).total_seconds())


async def maturity_loop() -> None:
    while True:
        try:
            count = await asyncio.to_thread(_run_once)
            if count:
                logger.info("Settled %d matured savings accounts", count)
        except Exception:
            logger.exception("Savings maturity loop iteration crashed")
        await asyncio.sleep(_seconds_until_next_run())
