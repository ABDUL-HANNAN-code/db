from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Notification(BaseModel):
    id: Optional[str] = None
    user_id: str
    notification_type: str
    title: str
    message: str
    read: bool = False
    created_at: datetime = datetime.utcnow()
