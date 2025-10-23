import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class AuthToken:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.security = HTTPBearer()

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a new JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)  # Default 30 min
            
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a new JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)  # 7 days
        to_encode.update({"exp": expire, "refresh": True})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("refresh"):
                raise HTTPException(
                    status_code=401,
                    detail="Cannot use refresh token for authentication"
                )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )

    def refresh_access_token(self, refresh_token: str) -> str:
        """Create new access token from refresh token"""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            if not payload.get("refresh"):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid refresh token"
                )
            
            # Remove refresh flag and expiry
            del payload["refresh"]
            if "exp" in payload:
                del payload["exp"]
                
            return self.create_access_token(payload)
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Refresh token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=401,
                detail="Could not validate refresh token"
            )

    async def __call__(self, request: Request) -> Dict[str, Any]:
        """Dependency for protected routes"""
        try:
            credentials: HTTPAuthorizationCredentials = await self.security(request)
            payload = self.decode_token(credentials.credentials)
            return payload
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=str(e)
            )

def get_token_handler(secret_key: str):
    """Create token handler instance"""
    return AuthToken(secret_key)

# Session management functions
class SessionManager:
    @staticmethod
    def create_session_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create session data from user information"""
        return {
            "user_id": user_data["id"],
            "email": user_data["email"],
            "role": user_data["user_metadata"]["role"],
            "first_time_login": user_data["user_metadata"].get("first_time_login", True),
            "profile_completed": user_data["user_metadata"].get("profile_completed", False)
        }

    @staticmethod
    def get_redirect_url(role: str, first_time_login: bool, profile_completed: bool) -> str:
        """Determine redirect URL based on user state"""
        if not profile_completed and first_time_login:
            if role == "recruiter":
                return "https://recruiter.skreenit.com/recruiter-profile.html"
            else:
                return "https://applicant.skreenit.com/detailed-application-form.html"
        else:
            if role == "recruiter":
                return "https://dashboard.skreenit.com/recruiter-dashboard.html"
            else:
                return "https://dashboard.skreenit.com/candidate-dashboard.html"