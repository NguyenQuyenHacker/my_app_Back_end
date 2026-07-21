import uuid
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.user_thread_model import UserThread
from app.models.user_model import User
from app.core.constants import SERVING_URL
import httpx


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_user_id_from_customer_id(session: Session, customer_id: uuid.UUID) -> uuid.UUID | None:
    user = session.exec(
        select(User).where(User.customer_id == customer_id)
    ).first()
    return user.user_id if user else None


def list_threads_by_user(session: Session, user_id: uuid.UUID) -> list[UserThread]:
    statement = (
        select(UserThread)
        .where(UserThread.user_id == user_id)
        .order_by(UserThread.updated_at.desc())
    )
    return list(session.exec(statement).all())


def create_user_thread(
    session: Session,
    user_id: uuid.UUID,
    thread_id: uuid.UUID,
    title: str | None = None,
) -> UserThread:
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


async def delete_thread_service(
    session: Session,
    user_id: uuid.UUID,
    thread_id: uuid.UUID,
):
    """
    1. Xóa ở AI Agent
    2. Xóa ở Postgres
    """
    row = get_owned_thread(session, user_id, thread_id)
    if not row:
        return False

    # Xóa hội thoại ở serving (Agents SDK): session_id = thread_id
    async with httpx.AsyncClient() as client:
        try:
            res = await client.delete(f"{SERVING_URL}/agent/sessions/{thread_id}")
            res.raise_for_status()
        except httpx.HTTPError as e:
            # Serving lỗi/đã xoá trước đó → vẫn xoá mapping ở DB
            print(f"Warning: Failed to delete session at serving: {e}")

    # Xóa DB
    session.delete(row)
    session.commit()
    return True


async def initialize_new_thread(
    session: Session,
    user_id: uuid.UUID,
    title: str | None = None,
) -> UserThread:
    """
    Agents SDK: session_id do serving tạo lazily ở tin nhắn đầu (SQLAlchemySession),
    nên BE chỉ cần tự sinh thread_id (uuid4) và lưu mapping — KHÔNG gọi agent server.
    """
    thread_id = uuid.uuid4()
    return create_user_thread(
        session=session,
        user_id=user_id,
        thread_id=thread_id,
        title=title,
    )


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