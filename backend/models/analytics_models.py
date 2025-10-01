from pydantic import BaseModel
from typing import Optional, Dict

class AnalyticsEventRequest(BaseModel):
    user_id: Optional[str] = None
    event_type: str
    event_data: Optional[Dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
