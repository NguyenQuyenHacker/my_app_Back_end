# app/core/constants.py
import os

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8123")

# Serving chatbot (Agents SDK) — process riêng, mặc định :2024.
# Dùng để dọn hội thoại khi xoá thread (session_id = thread_id).
SERVING_URL = os.getenv("SERVING_URL", "http://localhost:2024")
