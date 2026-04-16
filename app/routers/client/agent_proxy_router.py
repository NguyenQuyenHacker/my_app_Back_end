import httpx
from fastapi import APIRouter, Request, Depends
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
    """
    client = httpx.AsyncClient()
    
    # Render lại URL trỏ tới agent_url / path
    url = httpx.URL(f"{AGENT_URL}/{path}?{request.url.query}")
    
    # Đọc body từ request gửi lên
    body = await request.body()
    
    # Lọc các headers (bỏ host và content-length để client httpx tự sinh lại)
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    # Tạo request để gửi tới AI Agent
    req = client.build_request(
        method=request.method,
        url=url,
        headers=headers,
        content=body
    )
    
    # Gửi request với stream=True
    response = await client.send(req, stream=True)
    
    # Trả về kết nối streaming 
    return StreamingResponse(
        response.aiter_raw(),
        status_code=response.status_code,
        headers={
            k: v for k, v in response.headers.items() 
            if k.lower() not in ("content-length", "content-encoding", "transfer-encoding")
        },
        background=BackgroundTask(response.aclose)
    )
