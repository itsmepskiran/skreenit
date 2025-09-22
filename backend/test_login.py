from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

app = FastAPI()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/auth/login")
def login(payload: LoginRequest):
    print("🔐 /auth/login route triggered")
    if payload.email != "test@skreenit.com" or payload.password != "test123":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": "fake-token", "user": {"email": payload.email}}
