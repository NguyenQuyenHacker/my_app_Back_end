import os
from typing import Optional

from langchain_core.runnables import RunnableConfig

DEFAULT_API_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 30


def get_jwt(config: Optional[RunnableConfig]) -> Optional[str]:
    if config and "configurable" in config:
        return config["configurable"].get("jwt_token")
    return None


def api_base() -> str:
    return os.environ.get("API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")
