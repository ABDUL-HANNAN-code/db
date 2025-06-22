from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ActivityLog(BaseModel):
    id: Optional[str] = None
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()
