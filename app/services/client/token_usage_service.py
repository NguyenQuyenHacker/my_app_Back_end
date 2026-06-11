"""
Đếm & giới hạn token mỗi user theo ngày.

- Mỗi user (customer_id) chỉ được dùng tối đa DAILY_TOKEN_LIMIT token/ngày,
  cộng dồn qua TẤT CẢ thread.
- Lưu ở bảng `token_usage_daily` trong DB chính (DATABASE_URL / get_session).
- "Ngày" tính theo giờ Việt Nam (UTC+7, không DST).
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlmodel import Session

# Việt Nam = UTC+7 cố định (không có DST)
VN_TZ = timezone(timedelta(hours=7))

# Hạn mức token/ngày cho mỗi user
DAILY_TOKEN_LIMIT = 250_000


def today_vn():
    """Ngày hiện tại theo giờ Việt Nam."""
    return datetime.now(VN_TZ).date()


def next_reset_at() -> datetime:
    """Thời điểm reset hạn mức tiếp theo = 00:00 ngày mai (giờ VN)."""
    tomorrow = (datetime.now(VN_TZ) + timedelta(days=1)).date()
    return datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=VN_TZ)


def get_today_usage(session: Session, user_id: str) -> int:
    """Tổng token user đã dùng trong NGÀY HÔM NAY (giờ VN). Chưa có thì 0."""
    row = session.execute(
        text(
            "SELECT total_tokens FROM token_usage_daily "
            "WHERE user_id = :uid AND usage_date = :d"
        ),
        {"uid": str(user_id), "d": today_vn()},
    ).first()
    return int(row[0]) if row else 0


def is_over_limit(session: Session, user_id: str, limit: int = DAILY_TOKEN_LIMIT) -> bool:
    """True nếu user đã chạm/vượt hạn mức hôm nay."""
    return get_today_usage(session, user_id) >= limit


def add_usage(session: Session, user_id: str, delta_tokens: int) -> None:
    """
    Cộng dồn token cho user trong ngày hôm nay (UPSERT atomic, an toàn khi nhiều lượt đồng thời).
    delta_tokens <= 0 thì bỏ qua.
    """
    if not delta_tokens or delta_tokens <= 0:
        return
    session.execute(
        text(
            """
            INSERT INTO token_usage_daily
                (user_id, usage_date, total_tokens, message_count, updated_at)
            VALUES (:uid, :d, :delta, 1, now())
            ON CONFLICT (user_id, usage_date) DO UPDATE
            SET total_tokens  = token_usage_daily.total_tokens + EXCLUDED.total_tokens,
                message_count = token_usage_daily.message_count + 1,
                updated_at    = now()
            """
        ),
        {"uid": str(user_id), "d": today_vn(), "delta": int(delta_tokens)},
    )
    session.commit()
