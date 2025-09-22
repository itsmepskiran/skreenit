from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordChangedRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
