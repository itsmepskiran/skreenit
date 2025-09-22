from pydantic import BaseModel
from typing import List, Optional, Any

class DashboardSummary(BaseModel):
    role: str
    jobs: Optional[List[Any]] = None
    applications: Optional[List[Any]] = None
