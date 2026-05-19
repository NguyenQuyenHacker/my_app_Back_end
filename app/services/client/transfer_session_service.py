import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.enums import TransferType
from app.models.transfer_session_model import TransferSession

SESSION_TTL_MINUTES = 5


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_session(
    session: Session,
    *,
    customer_id: uuid.UUID,
    source_account_id: uuid.UUID,
    transfer_type: TransferType,
    payload: dict,
) -> TransferSession:
    now = _now()
    s = TransferSession(
        customer_id=customer_id,
        source_account_id=source_account_id,
        transfer_type=transfer_type,
        payload=payload,
        used=False,
        created_at=now,
        expires_at=now + timedelta(minutes=SESSION_TTL_MINUTES),
    )
    session.add(s)
    session.flush()
    session.refresh(s)
    return s


def load_active_session(
    session: Session,
    *,
    session_id: uuid.UUID,
    customer_id: uuid.UUID,
    transfer_type: TransferType,
) -> Optional[TransferSession]:
    s = session.exec(
        select(TransferSession).where(TransferSession.session_id == session_id).with_for_update()
    ).first()
    if not s:
        return None
    if s.customer_id != customer_id:
        return None
    if s.transfer_type != transfer_type:
        return None
    if s.used:
        return None
    if s.expires_at < _now():
        return None
    return s


def consume(session_obj: TransferSession) -> None:
    session_obj.used = True
