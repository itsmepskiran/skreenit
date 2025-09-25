from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    mobile: str
    location: str
    role: str  # "candidate" | "recruiter"
    company_id: Optional[str] = None


class PasswordChangedRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr
