from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    id: Optional[str] = None
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    quantum_level: int = 1
    total_capsules: int = 0
    unlocked_capsules: int = 0
    quantum_connections: List[str] = []

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    quantum_level: int
    total_capsules: int
    unlocked_capsules: int