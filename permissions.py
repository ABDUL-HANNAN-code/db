from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PermissionLevel(str, Enum):
    VIEW = "view"
    COMMENT = "comment"
    INTERACT = "interact"

class CapsulePermission(BaseModel):
    id: Optional[str] = None
    capsule_id: str
    owner_id: str
    shared_with_user_id: str
    permission_level: PermissionLevel
    granted_at: datetime = datetime.utcnow()
    expires_at: Optional[datetime] = None
    is_active: bool = True

class ShareRequest(BaseModel):
    capsule_id: str
    username: str
    permission_level: PermissionLevel
    message: Optional[str] = None
    expires_in_days: Optional[int] = None
