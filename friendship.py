from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"

class Friendship(BaseModel):
    id: Optional[str] = None
    requester_id: str
    addressee_id: str
    status: FriendshipStatus = FriendshipStatus.PENDING
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

class FriendRequest(BaseModel):
    addressee_username: str
    message: Optional[str] = None

class UserProfile(BaseModel):
    id: str
    username: str
    full_name: Optional[str] = None
    quantum_level: int
    is_online: bool = False
    last_seen: Optional[datetime] = None
