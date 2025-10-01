from pydantic import BaseModel
from typing import Optional

class NotificationRequest(BaseModel):
    user_id: str
    title: str
    message: str
    type: str
    related_id: Optional[str] = None
    is_read: Optional[bool] = False
