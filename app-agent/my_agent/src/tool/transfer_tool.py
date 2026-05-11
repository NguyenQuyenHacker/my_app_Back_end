import os
import requests
from pydantic import BaseModel, Field
from typing import Optional
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig

try:
    from langgraph.types import interrupt
except ImportError:
    # Fallback in case interrupt is not available
    def interrupt(payload):
        raise NotImplementedError("langgraph.types.interrupt is not available")

class TransferInput(BaseModel):
    receiver_bank_name: str = Field(description="Tên ngân hàng người nhận")
    receiver_name: str = Field(description="Tên người nhận")
    receiver_account_no: str = Field(description="Số tài khoản người nhận")
    amount: float = Field(description="Số tiền cần chuyển")
    description: Optional[str] = Field(None, description="Nội dung chuyển khoản")
    otp: Optional[str] = Field(None, description="Mã OTP người dùng cung cấp sẵn (nếu có)")

@tool("create_transfer_request", args_schema=TransferInput)
def create_transfer_request(
    receiver_bank_name: str,
    receiver_name: str,
    receiver_account_no: str,
    amount: float,
    description: Optional[str] = None,
    otp: Optional[str] = None,
    *,
    config: RunnableConfig = None
) -> str:
    """
    Công cụ để TẠO YÊU CẦU CHUYỂN TIỀN (Hiển thị giao diện xác nhận cho người dùng).
    Bất cứ khi nào người dùng muốn chuyển tiền, bạn PHẢI GỌI CÔNG CỤ NÀY NGAY LẬP TỨC.
    Tuyệt đối KHÔNG ĐƯỢC nhắn tin hỏi lại người dùng để xác nhận, vì công cụ này CHỈ tạo một form giao diện an toàn để người dùng tự kiểm tra và nhập OTP. Nó KHÔNG tự động chuyển tiền ngay, nên hoàn toàn an toàn để gọi.
    """
    
    # Ở kiến trúc mới sử dụng HumanInTheLoopMiddleware,
    # Khi hàm này thực sự được chạy, tức là người dùng đã phê duyệt trên UI.
    
    if not otp:
        return "Lỗi: Không nhận được mã OTP từ xác nhận của người dùng. Giao dịch bị hủy."

    # Lấy JWT token từ config (Frontend cần truyền token vào config.configurable.jwt_token khi chạy agent)
    jwt_token = None
    if config and "configurable" in config:
        jwt_token = config["configurable"].get("jwt_token")
        
    if not jwt_token:
        return "Lỗi: Không tìm thấy JWT token để xác thực giao dịch. Giao dịch bị hủy."

    # Cấu hình API endpoint (giả sử backend chạy ở localhost:8000)
    api_url = os.environ.get("API_BASE_URL", "http://localhost:8000") + "/transfer"
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "receiver_bank_name": receiver_bank_name,
        "receiver_name": receiver_name,
        "receiver_account_no": receiver_account_no,
        "amount": amount,
        "description": description or "Chuyển tiền",
        "otp": otp
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
    except requests.exceptions.RequestException as e:
        return f"Lỗi kết nối đến API chuyển khoản: {str(e)}"

    try:
        data = response.json()
    except ValueError:
        return f"Lỗi: API chuyển khoản trả về phản hồi không hợp lệ (HTTP {response.status_code}). Kiểm tra lại server backend."

    if response.status_code == 200:
        return f"Giao dịch thành công! Mã giao dịch: {data.get('transfer_id')}. Số dư mới: {float(data.get('new_balance', 0)):,.0f} VNĐ."
    else:
        error_msg = data.get("detail", str(data))
        return f"Giao dịch thất bại: {error_msg}"
