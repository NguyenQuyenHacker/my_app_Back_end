"""FastAPI serving cho agent bản Agents SDK — thay `langgraph dev`.

Streaming qua **WebSocket** (không dùng useStream của langchain nữa):
  WS   /agent/ws/chat/{session_id}?token=<jwt>   — chạy chat_agent, đẩy token/tool/done/error
REST quản lý hội thoại:
  GET    /agent/sessions
  POST   /agent/sessions
  GET    /agent/sessions/{id}/messages
  DELETE /agent/sessions/{id}

JWT: browser WebSocket KHÔNG set được Authorization header → truyền qua query param `token`.
"""
import asyncio
import json
import os
import sys

# Windows: psycopg (async, do langchain-postgres PGVectorStore ở tool RAG dùng) không chạy
# trên ProactorEventLoop. Ép SelectorEventLoop — PHẢI đặt trước khi tạo loop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Nạp .env TRƯỚC khi import agent_sdk/config/db (chúng đọc env ngay lúc import).
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from openai.types.responses import ResponseTextDeltaEvent
from agents import Runner

from my_agent.agent_sdk import chat_agent
from my_agent.src.context import ChatContext
from serving.sessions import (
    delete_session,
    get_session_messages,
    list_sessions,
    new_session_id,
)

# Núm tinh chỉnh hiệu ứng gõ chữ (chỉ làm mượt hiển thị, không đổi nội dung).
# Nhẹ tay: gói to hơn + delay nhỏ hơn -> tail nhanh ~4x mà vẫn mượt.
SMOOTH_CHARS = 6
SMOOTH_DELAY = 0.006

# transfer_init trả chuỗi mở đầu bằng marker này + JSON -> FE dùng để tự điền form & navigate.
TRANSFER_PENDING_MARKER = "[TRANSFER_PENDING]"


def _extract_transfer_payload(output: object) -> dict | None:
    """Rút JSON pending sau marker [TRANSFER_PENDING] trong output của transfer_init."""
    text = output if isinstance(output, str) else str(output)
    idx = text.find(TRANSFER_PENDING_MARKER)
    if idx < 0:
        return None
    after = text[idx + len(TRANSFER_PENDING_MARKER):]
    line = after.split("\n", 1)[0].strip()
    try:
        data = json.loads(line)
        return data if isinstance(data, dict) and data.get("session_id") else None
    except (json.JSONDecodeError, ValueError):
        return None


app = FastAPI(title="agent-serving (Agents SDK)")

# CORS: FE (Vite dev :5173) gọi REST cross-origin. Cho phép dev origin (WS không bị CORS).
_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup() -> None:
    # Tạo bảng session 1 lần (idempotent) + warm pool DB -> các truy vấn sau bỏ DDL thừa.
    from serving.db import ensure_tables
    await ensure_tables()


async def _send_smooth(ws: WebSocket, text: str) -> None:
    for i in range(0, len(text), SMOOTH_CHARS):
        await ws.send_text(json.dumps({"type": "token", "data": text[i : i + SMOOTH_CHARS]}))
        await asyncio.sleep(SMOOTH_DELAY)


# =========================
# CHAT (WebSocket streaming)
# =========================
@app.websocket("/agent/ws/chat/{session_id}")
async def ws_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    jwt = websocket.query_params.get("token")
    from serving.db import make_session  # import trễ để lỗi DB không chết app lúc khởi động
    session = make_session(session_id)
    try:
        while True:
            user_text = await websocket.receive_text()
            if not user_text.strip():
                continue
            result = Runner.run_streamed(
                chat_agent, user_text, session=session, context=ChatContext(jwt=jwt)
            )
            try:
                async for event in result.stream_events():
                    if event.type == "raw_response_event" and isinstance(
                        event.data, ResponseTextDeltaEvent
                    ):
                        await _send_smooth(websocket, event.data.delta)
                    elif event.type == "run_item_stream_event":
                        item = event.item
                        if item.type == "tool_call_item":
                            name = getattr(item.raw_item, "name", "?")
                            await websocket.send_text(json.dumps({"type": "tool", "name": name}))
                        elif item.type == "tool_call_output_item":
                            # transfer_init trả marker -> đẩy payload cho FE tự điền form & chuyển trang
                            payload = _extract_transfer_payload(getattr(item, "output", None))
                            if payload:
                                await websocket.send_text(
                                    json.dumps({"type": "transfer", "data": payload})
                                )
                await websocket.send_text(json.dumps({"type": "done"}))
            except Exception as e:  # noqa: BLE001 — báo client, giữ kết nối
                await websocket.send_text(
                    json.dumps({"type": "error", "data": f"{type(e).__name__}: {e}"})
                )
    except WebSocketDisconnect:
        pass


# =========================
# REST: quản lý session
# =========================
@app.get("/agent/sessions")
async def api_list_sessions():
    return await list_sessions()


@app.post("/agent/sessions")
async def api_create_session():
    return {"session_id": new_session_id()}


@app.get("/agent/sessions/{session_id}/messages")
async def api_get_messages(session_id: str):
    return await get_session_messages(session_id)


@app.delete("/agent/sessions/{session_id}")
async def api_delete_session(session_id: str):
    await delete_session(session_id)
    return {"ok": True}
