import uuid
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.user_thread_model import UserThread


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def list_threads_by_user(session: Session, user_id: uuid.UUID) -> list[UserThread]:
    statement = (
        select(UserThread)
        .where(UserThread.user_id == user_id)
        .order_by(UserThread.updated_at.desc())
    )
    return list(session.exec(statement).all())


def create_user_thread(session: Session, user_id: uuid.UUID, thread_id: uuid.UUID, title: str | None = None) -> UserThread:
    existing = session.exec(
        select(UserThread).where(
            UserThread.user_id == user_id,
            UserThread.thread_id == thread_id,
        )
    ).first()
    if existing:
        return existing

    row = UserThread(
        user_id=user_id,
        thread_id=thread_id,
        title=title or "Cuộc trò chuyện mới",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def get_owned_thread(
    session: Session,
    user_id: uuid.UUID,
    thread_id: uuid.UUID,
) -> UserThread | None:
    statement = select(UserThread).where(
        UserThread.user_id == user_id,
        UserThread.thread_id == thread_id,
    )
    return session.exec(statement).first()


def update_thread_title(
    session: Session,
    user_id: uuid.UUID,
    thread_id: uuid.UUID,
    title: str,
) -> UserThread | None:
    row = get_owned_thread(session, user_id, thread_id)
    if not row:
        return None

    row.title = title.strip() or "Cuộc trò chuyện mới"
    row.updated_at = utc_now()
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def touch_thread(
    session: Session,
    user_id: uuid.UUID,
    thread_id: uuid.UUID,
) -> UserThread | None:
    row = get_owned_thread(session, user_id, thread_id)
    if not row:
        return None

    row.updated_at = utc_now()
    session.add(row)
    session.commit()
    session.refresh(row)
    return row