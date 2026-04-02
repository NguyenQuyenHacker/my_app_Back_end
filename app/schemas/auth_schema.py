from pydantic import BaseModel, EmailStr


# user schemas--------------------------------------------------------------------------
class UserLogin(BaseModel):
    phone: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# admin schemas--------------------------------------------------------------------------
class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminInfoResponse(BaseModel):
    admin_id: str
    admin_name: str
    email: EmailStr
    role: str
    is_active: bool 
    last_login_at: str | None = None


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminInfoResponse