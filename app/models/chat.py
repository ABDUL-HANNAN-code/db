from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    CAPSULE_SHARE = "capsule_share"
    QUANTUM_STATE = "quantum_state"

class Conversation(BaseModel):
    id: Optional[str] = None
    participants: List[str]
    conversation_type: str = "private"
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: datetime = Field(default_factory=datetime.utcnow)
    quantum_encrypted: bool = False

class ChatMessage(BaseModel):
    id: Optional[str] = None
    conversation_id: str
    sender_id: str
    receiver_id: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "sent"
    reply_to: Optional[str] = None

class ChatMessageCreate(BaseModel):
    conversation_id: Optional[str] = None
    receiver_id: str
    message_type: MessageType = MessageType.TEXT
    content: Dict[str, Any]
    reply_to: Optional[str] = None

