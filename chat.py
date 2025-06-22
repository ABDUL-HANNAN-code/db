from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.models.chat import ChatMessage, Conversation, ChatMessageCreate
from app.services.chat_service import chat_service
from app.routers.auth import get_current_user
from app.models.user import UserResponse

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/messages", response_model=ChatMessage)
async def send_message(
    message_data: ChatMessageCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Send a chat message"""
    try:
        return await chat_service.send_message(current_user.id, message_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/conversations", response_model=List[Conversation])
async def get_conversations(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user's conversations"""
    return await chat_service.get_conversations(current_user.id)

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """Get messages from a conversation"""
    try:
        messages = await chat_service.get_conversation_messages(
            conversation_id, 
            current_user.id,
            limit,
            offset
        )
        return {"messages": [msg.dict() for msg in messages]}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/conversations/{conversation_id}/read")
async def mark_conversation_read(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Mark all messages in conversation as read"""
    await chat_service.mark_messages_as_read(conversation_id, current_user.id)
    return {"status": "success"}

@router.get("/online-users")
async def get_online_users(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get list of online users"""
    from app.services.connection_manager import connection_manager
    online_users = await connection_manager.get_online_users()
    return {"online_users": online_users}
