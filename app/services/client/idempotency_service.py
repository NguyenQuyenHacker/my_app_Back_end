import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.idempotency_key_model import IdempotencyKey

DEFAULT_TTL_HOURS = 24


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get_existing(session: Session, key: str, user_id: uuid.UUID) -> Optional[dict]:
    if not key:
        return None
    row = session.exec(
        select(IdempotencyKey).where(IdempotencyKey.key == key)
    ).first()
    if not row:
        return None
    if row.user_id != user_id:
        return None
    if row.expires_at < _now():
        return None
    if not row.response:
        return None
    try:
        return json.loads(row.response)
    except (TypeError, ValueError):
        return None


def save(
    session: Session,
    *,
    key: str,
    user_id: uuid.UUID,
    status_code: int,
    response_body: dict,
    ttl_hours: int = DEFAULT_TTL_HOURS,
) -> None:
    if not key:
        return
    now = _now()
    record = IdempotencyKey(
        key=key,
        user_id=user_id,
        status_code=status_code,
        response=json.dumps(response_body, default=str),
        created_at=now,
        expires_at=now + timedelta(hours=ttl_hours),
    )
    session.add(record)
    session.flush()
