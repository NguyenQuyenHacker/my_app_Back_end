from typing import Literal, Optional

import requests
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from my_agent.src.tool._http import REQUEST_TIMEOUT, api_base, get_jwt


def _fmt_vnd(value) -> str:
    if value is None:
        return "0"
    try:
        return f"{int(round(float(value))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(value)


def _fmt_dt(value: str) -> str:
    if not value:
        return ""
    try:
        from datetime import datetime
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(value)


# =========================
# TOOL 1: GET ACCOUNT BALANCE
# =========================
class GetAccountBalanceInput(BaseModel):
    reason: Optional[str] = Field(
        default=None,
        description="Lookup reason (optional, leave empty if none).",
    )


@tool("get_account_balance", args_schema=GetAccountBalanceInput)
def get_account_balance(reason: Optional[str] = None, *, config: RunnableConfig = None) -> str:
    """Look up the logged-in customer's main account balance. Needs NO input (reads the JWT).
    Returns: account number, current balance, held amount, available balance, status."""
    jwt_token = get_jwt(config)
    if not jwt_token:
        return "Lỗi: Không tìm thấy JWT token để xác thực."

    url = f"{api_base()}/api/account/balance"
    headers = {"Authorization": f"Bearer {jwt_token}"}

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        return f"Lỗi kết nối đến API tra cứu số dư: {str(e)}"

    try:
        data = response.json()
    except ValueError:
        return f"API tra cứu số dư trả về phản hồi không hợp lệ (HTTP {response.status_code})."

    if response.status_code != 200:
        detail = data.get("detail") if isinstance(data, dict) else str(data)
        return f"Lỗi khi tra cứu số dư: {detail}"

    if not data.get("has_account", True):
        return "Khách hàng hiện chưa có tài khoản nào trong hệ thống Techcombank."

    currency = data.get("currency") or "VND"
    status_note = ""
    if data.get("status") and data.get("status") != "ACTIVE":
        status_note = f"\n⚠️ Tài khoản đang ở trạng thái {data.get('status')} — vui lòng thông báo cho khách."

    return (
        f"Thông tin số dư tài khoản:\n"
        f"- Số tài khoản: {data.get('account_no')} ({data.get('bank_name')})\n"
        f"- Số dư hiện tại: {_fmt_vnd(data.get('balance'))} {currency}\n"
        f"- Đang phong toả: {_fmt_vnd(data.get('hold_amount'))} {currency}\n"
        f"- Có thể sử dụng: {_fmt_vnd(data.get('available_balance'))} {currency}\n"
        f"- Trạng thái: {data.get('status')}"
        f"{status_note}"
    )


# =========================
# TOOL 2: GET TRANSACTION HISTORY
# =========================
class GetTransactionHistoryInput(BaseModel):
    limit: int = Field(
        default=5, ge=1, le=20,
        description="Max transactions to return (default 5, max 20).",
    )
    direction: Literal["IN", "OUT", "ALL"] = Field(
        default="ALL",
        description="IN = money received; OUT = money sent; ALL = both.",
    )
    date_from: Optional[str] = Field(
        default=None,
        description="Start date YYYY-MM-DD; empty if no time range.",
    )
    date_to: Optional[str] = Field(
        default=None,
        description="End date YYYY-MM-DD inclusive; empty if no time range.",
    )
    min_amount: Optional[float] = Field(
        default=None, ge=0,
        description="Only amount >= this (VND). E.g. 'trên 5 triệu' -> 5000000.",
    )
    max_amount: Optional[float] = Field(
        default=None, ge=0,
        description="Only amount <= this (VND).",
    )


@tool("get_transaction_history", args_schema=GetTransactionHistoryInput)
def get_transaction_history(
    limit: int = 5,
    direction: str = "ALL",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    *,
    config: RunnableConfig = None,
) -> str:
    """Look up the logged-in customer's SUCCESSFUL transaction history.
    Returns matching transactions (datetime, direction, amount, counterparty, description).
    Call with no arguments for the 5 most recent. See the system prompt for mapping
    Vietnamese time/amount phrases to the parameters below."""
    jwt_token = get_jwt(config)
    if not jwt_token:
        return "Lỗi: Không tìm thấy JWT token để xác thực."

    params: dict = {"limit": limit, "direction": direction}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    if min_amount is not None:
        params["min_amount"] = min_amount
    if max_amount is not None:
        params["max_amount"] = max_amount

    url = f"{api_base()}/api/account/transactions"
    headers = {"Authorization": f"Bearer {jwt_token}"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        return f"Lỗi kết nối đến API lịch sử giao dịch: {str(e)}"

    try:
        data = response.json()
    except ValueError:
        return f"API lịch sử giao dịch trả về phản hồi không hợp lệ (HTTP {response.status_code})."

    if response.status_code != 200:
        detail = data.get("detail") if isinstance(data, dict) else str(data)
        return f"Lỗi khi tra cứu lịch sử giao dịch: {detail}"

    txns = data.get("transactions", [])
    count = data.get("count", 0)
    filters_echo = data.get("filters", {})

    if count == 0:
        return (
            f"Không có giao dịch nào khớp điều kiện (filter: {filters_echo}). "
            f"Gợi ý cho khách: thử nới rộng khoảng ngày, bỏ bớt min/max amount, hoặc đổi direction."
        )

    lines = [f"Tìm thấy {count} giao dịch (filter áp dụng: {filters_echo}):"]
    for t in txns:
        is_in = t.get("direction") == "IN"
        sign = "+" if is_in else "-"
        bank = f" - {t.get('counterparty_bank')}" if t.get("counterparty_bank") else ""
        cp_acc = t.get("counterparty_account") or "?"
        cp_name = t.get("counterparty_name") or "(không rõ tên)"
        desc = t.get("description") or "(không có nội dung)"
        currency = t.get("currency") or "VND"
        lines.append(
            f"- {_fmt_dt(t.get('created_at'))} | {sign}{_fmt_vnd(t.get('amount'))} {currency} "
            f"| {cp_name} ({cp_acc}{bank}) | \"{desc}\" | {t.get('transaction_code')}"
        )

    return "\n".join(lines)
