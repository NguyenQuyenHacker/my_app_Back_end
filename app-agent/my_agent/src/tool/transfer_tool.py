import json
from typing import Optional

import requests
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from my_agent.src.bank_codes import BANK_CODES, normalize_bank_code
from my_agent.src.tool._http import REQUEST_TIMEOUT, api_base, get_jwt

INTERNAL_BANK_CODE = "TCB"
TRANSFER_PENDING_MARKER = "[TRANSFER_PENDING]"


# =========================
# TOOL 1: LOOKUP RECIPIENT
# =========================
class LookupRecipientInput(BaseModel):
    bank_input: str = Field(
        description="Bank name or code as entered by the user, passed VERBATIM (even if misspelled, e.g. 'Vietcombank', 'vcb', 'tech combank', 'vietcomback'). The tool normalizes it."
    )
    account_no: str = Field(description="Recipient account number")


@tool("lookup_recipient", args_schema=LookupRecipientInput)
def lookup_recipient(
    bank_input: str,
    account_no: str,
    *,
    config: RunnableConfig = None,
) -> str:
    """STEP 1 (mandatory before a transfer): verify the recipient exists in the DB.
    Normalizes the bank name/code (typos, abbreviations, no diacritics) and classifies internal (TCB) vs external.
    After it returns the recipient info, summarize for the customer and WAIT for confirmation before transfer_init."""
    bank_code = normalize_bank_code(bank_input)
    if not bank_code:
        supported = ", ".join(f"{c} ({BANK_CODES[c]['name']})" for c in BANK_CODES)
        return (
            f"Không nhận diện được ngân hàng '{bank_input}'. "
            f"Vui lòng kiểm tra lại. Các ngân hàng hỗ trợ: {supported}."
        )

    jwt_token = get_jwt(config)
    if not jwt_token:
        return "Lỗi: Không tìm thấy JWT token để xác thực."

    is_internal = bank_code == INTERNAL_BANK_CODE
    transfer_type = "internal" if is_internal else "external"
    bank_full = BANK_CODES[bank_code]["name"]

    headers = {"Authorization": f"Bearer {jwt_token}"}
    if is_internal:
        url = f"{api_base()}/api/transfer/lookup/internal"
        params = {"account_no": account_no}
    else:
        url = f"{api_base()}/api/transfer/lookup/external"
        params = {"bank_code": bank_code, "account_number": account_no}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        return f"Lỗi kết nối đến API lookup: {str(e)}"

    try:
        data = response.json()
    except ValueError:
        return f"API lookup trả về phản hồi không hợp lệ (HTTP {response.status_code})."

    if response.status_code != 200:
        detail = data.get("detail") if isinstance(data, dict) else str(data)
        return (
            f"Không tìm thấy tài khoản {account_no} tại {bank_full} ({bank_code}). "
            f"Chi tiết: {detail}. Vui lòng kiểm tra lại."
        )

    return (
        f"Đã tìm thấy người nhận trong DB:\n"
        f"- Tên: {data.get('full_name')}\n"
        f"- Ngân hàng: {bank_full} (mã chuẩn: {bank_code})\n"
        f"- Số TK: {data.get('account_no')}\n"
        f"- Loại chuyển khoản: {transfer_type}\n\n"
        f"Hãy tóm tắt thông tin trên cho khách hàng và HỎI xác nhận trước khi tiến hành. "
        f"Khi khách xác nhận, gọi transfer_init với receiver_bank_code='{bank_code}' "
        f"và receiver_account_no='{data.get('account_no')}'."
    )


# =========================
# TOOL 2: TRANSFER INIT
# =========================
class TransferInitInput(BaseModel):
    receiver_bank_code: str = Field(
        description="Recipient bank code (SHORT code, e.g. TCB / VCB / BIDV). Taken from the lookup_recipient result."
    )
    receiver_account_no: str = Field(description="Recipient account number (from lookup_recipient)")
    amount: float = Field(gt=0, description="Amount to transfer (VND)")
    description: Optional[str] = Field(default=None, description="Transfer description/note")


@tool("transfer_init", args_schema=TransferInitInput)
def transfer_init(
    receiver_bank_code: str,
    receiver_account_no: str,
    amount: float,
    description: Optional[str] = None,
    *,
    config: RunnableConfig = None,
) -> str:
    """STEP 2 (after lookup_recipient + customer confirmation): initialize the transfer session.
    On success the UI AUTOMATICALLY shows the confirmation form and collects the OTP.
    Never ask for the OTP and never call more tools — just summarize and wait for the result."""
    jwt_token = get_jwt(config)
    if not jwt_token:
        return "Lỗi: Không tìm thấy JWT token để xác thực giao dịch."

    bank_code = normalize_bank_code(receiver_bank_code)
    if not bank_code:
        return (
            f"Mã ngân hàng '{receiver_bank_code}' không hợp lệ. "
            f"Hãy gọi lookup_recipient trước để xác định mã chuẩn."
        )

    is_internal = bank_code == INTERNAL_BANK_CODE
    transfer_type = "internal" if is_internal else "external"

    if is_internal:
        url = f"{api_base()}/api/transfer/internal/init"
        payload = {
            "to_account_no": receiver_account_no,
            "amount": str(amount),
            "description": description,
        }
    else:
        url = f"{api_base()}/api/transfer/external/init"
        payload = {
            "to_bank_code": bank_code,
            "to_account_number": receiver_account_no,
            "amount": str(amount),
            "description": description,
        }

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        return f"Lỗi kết nối đến API khởi tạo chuyển khoản: {str(e)}"

    try:
        data = response.json()
    except ValueError:
        return f"API trả về phản hồi không hợp lệ (HTTP {response.status_code})."

    if response.status_code != 200:
        detail = data.get("detail") if isinstance(data, dict) else str(data)
        return f"Khởi tạo chuyển khoản thất bại: {detail}"

    pending = {
        "session_id": data.get("session_id"),
        "transfer_type": transfer_type,
        "to_name": data.get("to_name"),
        "to_account_no": data.get("to_account_no"),
        "to_bank_code": data.get("to_bank_code") or bank_code,
        "amount": str(data.get("amount")),
        "fee": str(data.get("fee")),
        "description": data.get("description"),
        "expires_at": data.get("expires_at"),
    }
    marker_line = f"{TRANSFER_PENDING_MARKER}{json.dumps(pending, ensure_ascii=False)}"

    return (
        f"{marker_line}\n\n"
        f"Đã khởi tạo phiên chuyển khoản ({transfer_type}):\n"
        f"- Người nhận: {pending['to_name']} ({pending['to_bank_code']} - {pending['to_account_no']})\n"
        f"- Số tiền: {pending['amount']} VNĐ\n"
        f"- Phí: {pending['fee']} VNĐ\n"
        f"- Nội dung: {pending['description'] or '(không có)'}\n"
        f"- Hết hạn: {pending['expires_at']}\n\n"
        f"Hệ thống đã TỰ ĐỘNG chuyển khách sang trang chuyển khoản và ĐIỀN SẴN toàn bộ thông tin trên. "
        f"Việc của bạn: báo cho khách biết bạn đã điền hộ thông tin, chỉ cần nhập OTP để hoàn tất. "
        f"KHÔNG xin OTP trong chat, KHÔNG gọi thêm tool."
    )
