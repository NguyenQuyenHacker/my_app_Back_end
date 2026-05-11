import json
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from app.core.constants import AGENT_URL
from app.core.dependencies import CurrentUserDep

router = APIRouter(prefix="/chat/agent", tags=["agent-proxy"])

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_langgraph_agent(path: str, request: Request, current_customer: CurrentUserDep):
    """
    Transparent Reverse Proxy cho LangGraph AI Agent.
    Bảo vệ bằng CurrentUserDep, chỉ cho phép request có chứa Token hợp lệ đi qua.
    Hỗ trợ luồng Server-Sent Events (SSE) để generate câu trả lời Token-by-Token.
    Tự động inject jwt_token vào config.configurable để các tool có thể dùng.
    """
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

    return StreamingResponse(
        response.aiter_raw(),
        status_code=response.status_code,
        media_type="text/event-stream",
        headers={
            k: v for k, v in response.headers.items()
            if k.lower() not in ("content-length", "content-encoding", "transfer-encoding", "content-type")
        },
        background=BackgroundTask(response.aclose),
    )
