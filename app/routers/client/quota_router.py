from fastapi import APIRouter

from app.core.dependencies import CurrentUserDep, SessionDep
from app.services.client.token_usage_service import (
    DAILY_TOKEN_LIMIT,
    get_today_usage,
    next_reset_at,
)

router = APIRouter(prefix="/chat", tags=["chat-quota"])


@router.get("/quota")
def get_my_quota(current_customer: CurrentUserDep, session: SessionDep):
    """Hạn mức token hôm nay của user đang đăng nhập (dùng cho FE hiển thị/disable)."""
    used = get_today_usage(session, str(current_customer.customer_id))
    remaining = max(0, DAILY_TOKEN_LIMIT - used)
    return {
        "used": used,
        "limit": DAILY_TOKEN_LIMIT,
        "remaining": remaining,
        "is_exceeded": used >= DAILY_TOKEN_LIMIT,
        "reset_at": next_reset_at().isoformat(),
    }
