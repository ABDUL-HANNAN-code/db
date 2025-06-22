from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class CapsuleType(str, Enum):
    MEMORY = "memory"
    MESSAGE = "message"
    IMAGE = "image"
    QUANTUM_STATE = "quantum_state"

class CapsuleStatus(str, Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    EXPIRED = "expired"

class TemporalCapsule(BaseModel):
    id: Optional[str] = None
    user_id: str
    title: str
    description: Optional[str] = None
    capsule_type: CapsuleType
    content: Dict[str, Any]
    unlock_date: datetime
    created_at: datetime = datetime.utcnow()
    status: CapsuleStatus = CapsuleStatus.LOCKED
    tags: List[str] = []

class CapsuleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    capsule_type: CapsuleType
    content: Dict[str, Any]
    unlock_date: datetime
    tags: List[str] = []
