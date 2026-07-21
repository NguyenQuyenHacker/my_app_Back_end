"""Session store cho Agents SDK — 1 async engine chung + helper tạo SQLAlchemySession.

DB lưu hội thoại (thay checkpoint .pckl của LangGraph). Đọc SESSION_DATABASE_URL (fallback
DATABASE_URL) và tự chuẩn hoá scheme cho asyncpg để dán URL Neon thô kiểu gì cũng chạy.
"""
import os
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from sqlalchemy.ext.asyncio import create_async_engine
from agents.extensions.memory import SQLAlchemySession


def _normalize_async_url(url: str) -> str:
    """Ép +asyncpg, sslmode→ssl, bỏ channel_binding (asyncpg không hiểu 2 cái này)."""
    if not url:
        return url
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            url = "postgresql+asyncpg://" + url[len(prefix):]
            break
    p = urlsplit(url)
    q = []
    for k, v in parse_qsl(p.query, keep_blank_values=True):
        if k == "channel_binding":
            continue
        if k == "sslmode":
            q.append(("ssl", v))
            continue
        q.append((k, v))
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))


SESSION_DATABASE_URL = _normalize_async_url(
    os.getenv("SESSION_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
)
if not SESSION_DATABASE_URL:
    raise RuntimeError(
        "Thiếu SESSION_DATABASE_URL (Postgres lưu hội thoại Agents SDK). "
        "Đặt trong .env, dạng postgresql://user:pass@host/db (tự chuẩn hoá sang asyncpg)."
    )

# Pool tái dùng kết nối tới Neon. pool_pre_ping xử lý trường hợp Neon thả kết nối idle
# (ping rẻ ~50ms trước khi dùng, tránh lỗi "connection closed"). pool_recycle < idle-timeout.
engine = create_async_engine(
    SESSION_DATABASE_URL,
    pool_size=5,
    max_overflow=5,
    pool_recycle=1800,
    pool_pre_ping=True,
)


def make_session(session_id: str) -> SQLAlchemySession:
    """Session gắn 1 hội thoại. create_tables=False -> KHÔNG chạy DDL mỗi lần (tiết kiệm
    ~450ms/truy vấn tới Neon). Bảng đã được tạo 1 lần qua ensure_tables() lúc startup."""
    return SQLAlchemySession(session_id, engine=engine, create_tables=False)


async def ensure_tables() -> None:
    """Khởi động: tạo bảng session 1 lần (idempotent) + warm kết nối pool."""
    from sqlalchemy import text
    await SQLAlchemySession("__bootstrap__", engine=engine, create_tables=True).get_items()
    async with engine.connect() as c:
        await c.execute(text("SELECT count(*) FROM agent_messages"))
