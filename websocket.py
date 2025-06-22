from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.services.connection_manager import connection_manager
from app.utils.security import verify_token
from app.utils.redis_client import redis_client
import asyncio
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_current_user_ws(websocket: WebSocket, token: str = Query(...)):
    """Get current user from WebSocket token"""
    try:
        payload = verify_token(token)
        if payload is None:
            await websocket.close(code=1008)
            return None
        
        user_id = payload.get("sub")
        if user_id is None:
            await websocket.close(code=1008)
            return None
        
        return user_id
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=1008)
        return None

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """Main WebSocket endpoint for real-time communication"""
    user_id = await get_current_user_ws(websocket, token)
    if not user_id:
        return
    
    await connection_manager.connect(websocket, user_id)
    
    try:
        # Start Redis message listener task
        redis_task = asyncio.create_task(redis_message_listener(websocket, user_id))
        websocket_task = asyncio.create_task(websocket_message_handler(websocket, user_id))
        
        # Wait for either task to complete
        done, pending = await asyncio.wait(
            [redis_task, websocket_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel remaining tasks
        for task in pending:
            task.cancel()
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        await connection_manager.disconnect(websocket, user_id)

async def redis_message_listener(websocket: WebSocket, user_id: str):
    """Listen for Redis pub/sub messages and forward to WebSocket"""
    try:
        while True:
            message = await redis_client.get_message()
            if message:
                await websocket.send_text(json.dumps(message))
            await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
    except Exception as e:
        logger.error(f"Redis listener error for user {user_id}: {e}")

async def websocket_message_handler(websocket: WebSocket, user_id: str):
    """Handle incoming WebSocket messages"""
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            message_type = message.get("type")
            
            if message_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message_type == "typing":
                await handle_typing_indicator(user_id, message)
            elif message_type == "mark_read":
                await handle_mark_read(user_id, message)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket message handler error for user {user_id}: {e}")

async def handle_typing_indicator(user_id: str, message: dict):
    """Handle typing indicator"""
    conversation_id = message.get("conversation_id")
    if conversation_id:
        typing_data = {
            "type": "typing_indicator",
            "user_id": user_id,
            "conversation_id": conversation_id,
            "is_typing": message.get("is_typing", True)
        }
        await connection_manager.send_to_conversation(
            conversation_id,
            typing_data,
            exclude_user=user_id
        )

async def handle_mark_read(user_id: str, message: dict):
    """Handle mark messages as read"""
    from app.services.chat_service import chat_service
    
    conversation_id = message.get("conversation_id")
    if conversation_id:
        await chat_service.mark_messages_as_read(conversation_id, user_id)
