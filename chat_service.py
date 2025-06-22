from app.models.chat import ChatMessage, Conversation, ChatMessageCreate
from app.database import get_database
from app.services.connection_manager import connection_manager
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

class ChatService:
    def __init__(self):
        self.db_name = "conversations"
        self.messages_db = "chat_messages"
    
    async def create_conversation(self, participants: List[str], conversation_type: str = "private", title: Optional[str] = None) -> Conversation:
        """Create a new conversation"""
        db = await get_database()
        
        # Check if private conversation already exists
        if conversation_type == "private" and len(participants) == 2:
            existing = await db[self.db_name].find_one({
                "participants": {"$all": participants, "$size": 2},
                "conversation_type": "private"
            })
            if existing:
                existing["id"] = str(existing["_id"])
                return Conversation(**existing)
        
        conversation_data = {
            "participants": participants,
            "conversation_type": conversation_type,
            "title": title,
            "created_at": datetime.utcnow(),
            "last_message_at": datetime.utcnow(),
            "quantum_encrypted": False
        }
        
        result = await db[self.db_name].insert_one(conversation_data)
        conversation_data["id"] = str(result.inserted_id)
        
        return Conversation(**conversation_data)
    
    async def send_message(self, sender_id: str, message_data: ChatMessageCreate) -> ChatMessage:
        """Send a chat message"""
        db = await get_database()
        
        # Create or get conversation
        if message_data.conversation_id:
            conversation_id = message_data.conversation_id
        else:
            # Create new conversation for private message
            participants = [sender_id, message_data.receiver_id]
            conversation = await self.create_conversation(participants)
            conversation_id = conversation.id
        
        # Create message
        message_doc = {
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "receiver_id": message_data.receiver_id,
            "message_type": message_data.message_type,
            "content": message_data.content,
            "timestamp": datetime.utcnow(),
            "status": "sent",
            "reply_to": message_data.reply_to
        }
        
        result = await db[self.messages_db].insert_one(message_doc)
        message_doc["id"] = str(result.inserted_id)
        
        # Update conversation last message time
        await db[self.db_name].update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {"last_message_at": datetime.utcnow()}}
        )
        
        # Send real-time notification
        chat_message = ChatMessage(**message_doc)
        await self._send_real_time_message(chat_message)
        
        return chat_message
    
    async def get_conversations(self, user_id: str) -> List[Conversation]:
        """Get user's conversations"""
        db = await get_database()
        
        conversations = []
        cursor = db[self.db_name].find({
            "participants": user_id
        }).sort("last_message_at", -1)
        
        async for conv in cursor:
            conv["id"] = str(conv["_id"])
            conversations.append(Conversation(**conv))
        
        return conversations
    
    async def get_conversation_messages(self, conversation_id: str, user_id: str, limit: int = 50, offset: int = 0) -> List[ChatMessage]:
        """Get messages from a conversation"""
        db = await get_database()
        
        # Verify user is participant
        conversation = await db[self.db_name].find_one({
            "_id": ObjectId(conversation_id),
            "participants": user_id
        })
        
        if not conversation:
            raise ValueError("Conversation not found or access denied")
        
        messages = []
        cursor = db[self.messages_db].find({
            "conversation_id": conversation_id
        }).sort("timestamp", -1).skip(offset).limit(limit)
        
        async for msg in cursor:
            msg["id"] = str(msg["_id"])
            messages.append(ChatMessage(**msg))
        
        return messages
    
    async def mark_messages_as_read(self, conversation_id: str, user_id: str):
        """Mark messages as read"""
        db = await get_database()
        
        await db[self.messages_db].update_many(
            {
                "conversation_id": conversation_id,
                "sender_id": {"$ne": user_id},
                "status": {"$ne": "read"}
            },
            {
                "$set": {"status": "read"}
            }
        )
    
    async def _send_real_time_message(self, message: ChatMessage):
        """Send real-time message notification"""
        message_data = {
            "type": "new_message",
            "message": message.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to conversation participants
        await connection_manager.send_to_conversation(
            message.conversation_id,
            message_data,
            exclude_user=message.sender_id
        )

chat_service = ChatService()
