import json
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

from sqlmodel import Session

from app.core.constants import AGENT_URL
from app.core.dependencies import CurrentUserDep
from app.db.database import engine
from app.services.client.token_usage_service import (
    DAILY_TOKEN_LIMIT,
    add_usage,
    is_over_limit,
)

router = APIRouter(prefix="/chat/agent", tags=["agent-proxy"])


# =========================
# HELPERS cho giới hạn token
# =========================
def _is_run_request(method: str, path: str) -> bool:
    """Request 'gửi tin nhắn' (tốn token) = POST tới .../runs hoặc .../runs/stream."""
    return method == "POST" and (path.endswith("runs/stream") or path.endswith("runs"))


def _extract_thread_id(path: str) -> str | None:
    """Lấy thread_id từ path dạng threads/{thread_id}/runs/stream."""
    parts = path.split("/")
    if "threads" in parts:
        i = parts.index("threads")
        if i + 1 < len(parts):
            return parts[i + 1]
    return None


def _last_turn_tokens(messages: list) -> int:
    """
    Tổng total_tokens của các AI message thuộc LƯỢT vừa rồi
    (= các message sau HumanMessage cuối cùng). Đếm đúng cả khi lượt có gọi tool
    (1 lượt sinh nhiều AI message).
    """
    total = 0
    for m in reversed(messages):
        t = m.get("type")
        if t == "human":
            break
        if t == "ai":
            um = m.get("usage_metadata") or {}
            total += int(um.get("total_tokens") or 0)
    return total


def _check_over(user_id: str) -> bool:
    with Session(engine) as s:
        return is_over_limit(s, user_id)


def _write_usage(user_id: str, delta: int) -> None:
    with Session(engine) as s:
        add_usage(s, user_id, delta)


async def _meter_after_stream(response, thread_id, user_id):
    """
    Chạy SAU khi stream trả lời xong (background): đóng kết nối upstream + đếm token.
    Mọi lỗi đếm đều nuốt — KHÔNG được làm hỏng luồng chat.
    """
    try:
        await response.aclose()
    except Exception:
        pass

    if not thread_id:
        return
    try:
        # Cách 1: đọc lại state thread từ agent (chỉ đọc DB của LangGraph, KHÔNG gọi Gemini)
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{AGENT_URL}/threads/{thread_id}/state")
        messages = (r.json().get("values") or {}).get("messages", [])
        delta = _last_turn_tokens(messages)
        if delta > 0:
            await run_in_threadpool(_write_usage, str(user_id), delta)
    except Exception:
        pass


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_langgraph_agent(path: str, request: Request, current_customer: CurrentUserDep):
    """
    Transparent Reverse Proxy cho LangGraph AI Agent.
    Bảo vệ bằng CurrentUserDep, chỉ cho phép request có chứa Token hợp lệ đi qua.
    Hỗ trợ luồng Server-Sent Events (SSE) để generate câu trả lời Token-by-Token.
    Tự động inject jwt_token vào config.configurable để các tool có thể dùng.

    NGOÀI RA: giới hạn token/ngày cho mỗi user — chặn nếu đã hết hạn mức,
    và đếm token sau mỗi lượt chat (xem token_usage_service).
    """
    user_id = str(current_customer.customer_id)
    is_run = _is_run_request(request.method, path)

    # --- CHẶN: nếu là lượt gửi tin mới và user đã hết hạn mức hôm nay ---
    if is_run and await run_in_threadpool(_check_over, user_id):
        return JSONResponse(
            status_code=429,
            content={
                "detail": (
                    f"Bạn đã đạt giới hạn {DAILY_TOKEN_LIMIT:,} token cho hôm nay. "
                    "Vui lòng quay lại vào ngày mai."
                )
            },
        )

    # Extract JWT token from Authorization header
    auth_header = request.headers.get("authorization", "")
    jwt_token = auth_header[7:] if auth_header.lower().startswith("bearer ") else None

    # Read body and inject jwt_token into config.configurable for POST/PUT/PATCH
    body_bytes = await request.body()
    if jwt_token and body_bytes and request.method in ("POST", "PUT", "PATCH"):
        try:
            body_json = json.loads(body_bytes)
            body_json.setdefault("config", {}).setdefault("configurable", {})["jwt_token"] = jwt_token
            body_bytes = json.dumps(body_json).encode()
        except (json.JSONDecodeError, AttributeError):
            pass  # Not JSON body, forward as-is

    url = httpx.URL(f"{AGENT_URL}/{path}?{request.url.query}")

    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)

    client = httpx.AsyncClient(timeout=600.0)
    req = client.build_request(
        method=request.method,
        url=url,
        headers=headers,
        content=body_bytes,
    )

    response = await client.send(req, stream=True)

    # --- ĐẾM: nếu là lượt chat, sau khi stream xong thì đếm token; ngược lại chỉ đóng kết nối ---
    if is_run:
        thread_id = _extract_thread_id(path)
        background = BackgroundTask(_meter_after_stream, response, thread_id, user_id)
    else:
        background = BackgroundTask(response.aclose)

    return StreamingResponse(
        response.aiter_raw(),
        status_code=response.status_code,
        media_type="text/event-stream",
        headers={
            k: v for k, v in response.headers.items()
            if k.lower() not in ("content-length", "content-encoding", "transfer-encoding", "content-type")
        },
        background=background,
    )
