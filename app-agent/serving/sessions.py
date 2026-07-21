"""Quản lý session_id: list / tạo mới / nạp lịch sử / xoá.

Bảng agent_sessions & agent_messages do SQLAlchemySession của SDK tự tạo & quản. Ở đây CHỈ
đọc để list/nạp và xoá theo session_id (FK ON DELETE CASCADE tự dọn messages). Không tự ghi.
"""
import json
import uuid

from sqlalchemy import text

from serving.db import engine, make_session

TITLE_MAX_LEN = 45


def new_session_id() -> str:
    return "sess-" + uuid.uuid4().hex[:20]


def _content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text") or block.get("content") or "")
            else:
                parts.append(str(block))
        return "".join(parts)
    return ""


def _derive_title(message_data: str) -> str:
    try:
        data = json.loads(message_data)
    except (json.JSONDecodeError, TypeError):
        return "Hội thoại mới"
    text_val = _content_to_text(data.get("content")).strip().replace("\n", " ")
    if not text_val:
        return "Hội thoại mới"
    return text_val[:TITLE_MAX_LEN] + ("…" if len(text_val) > TITLE_MAX_LEN else "")


async def list_sessions() -> list[dict]:
    async with engine.connect() as conn:
        sess_rows = (
            await conn.execute(
                text(
                    "SELECT session_id, created_at, updated_at "
                    "FROM agent_sessions ORDER BY updated_at DESC"
                )
            )
        ).fetchall()
        first_rows = (
            await conn.execute(
                text(
                    "SELECT DISTINCT ON (session_id) session_id, message_data "
                    "FROM agent_messages ORDER BY session_id, created_at ASC"
                )
            )
        ).fetchall()

    titles = {sid: _derive_title(md) for sid, md in first_rows}
    return [
        {
            "session_id": sid,
            "title": titles.get(sid, "Hội thoại mới"),
            "created_at": created.isoformat(),
            "updated_at": updated.isoformat(),
        }
        for sid, created, updated in sess_rows
    ]


async def get_session_messages(session_id: str) -> list[dict]:
    session = make_session(session_id)
    items = await session.get_items()
    out = []
    for item in items:
        role = item.get("role")
        if role not in ("user", "assistant"):
            continue
        content = _content_to_text(item.get("content")).strip()
        if content:
            out.append({"role": role, "content": content})
    return out


async def delete_session(session_id: str) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM agent_sessions WHERE session_id = :sid"),
            {"sid": session_id},
        )
