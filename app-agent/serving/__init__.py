"""Tầng serving bản OpenAI Agents SDK — thay vai trò của `langgraph dev`.

Chạy `chat_agent` (my_agent/agent_sdk.py) qua Runner + SQLAlchemySession, expose HTTP
(SSE streaming + REST session). JWT nhận từ Authorization header → ChatContext.
"""
