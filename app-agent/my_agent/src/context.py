"""Run context cho agent bản OpenAI Agents SDK.

Trong bản LangGraph, JWT đi qua `RunnableConfig["configurable"]["jwt_token"]`.
Ở Agents SDK, dữ liệu per-run đi qua `RunContextWrapper.context` (object tự định nghĩa,
KHÔNG gửi cho model). Lớp vỏ tool sẽ đọc `ctx.context.jwt` rồi dựng lại `config` dict
mà @tool LangChain gốc mong đợi.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ChatContext:
    """Truyền vào Runner.run(..., context=ChatContext(jwt=...))."""
    jwt: Optional[str] = None
