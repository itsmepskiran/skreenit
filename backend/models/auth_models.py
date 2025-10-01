from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    fullname: str
    email: EmailStr
    mobile: str
    location: str
    role: str  # e.g. 'candidate' or 'recruiter'
    company_id: Optional[str] = None

class PasswordChangedRequest(BaseModel):
    email: EmailStr
    fullname: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr
