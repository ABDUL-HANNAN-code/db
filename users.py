from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
from app.database import get_database
from app.routers.auth import get_current_user
from app.models.user import UserResponse
from bson import ObjectId
from datetime import datetime
import os
import shutil
from PIL import Image
import uuid

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get current user's profile"""
    return current_user

@router.put("/profile")
async def update_user_profile(
    full_name: Optional[str] = Form(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Update user profile"""
    db = await get_database()
    
    update_data = {}
    if full_name is not None:
        update_data["full_name"] = full_name
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": update_data}
        )
    
    return {"status": "updated"}

@router.post("/avatar")
async def upload_avatar(
    avatar: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload user avatar"""
    # Validate file type
    if not avatar.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads/avatars"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(avatar.filename)[1]
    filename = f"{current_user.id}_{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(avatar.file, buffer)
    
    # Resize image
    try:
        with Image.open(file_path) as img:
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            img.save(file_path, optimize=True, quality=85)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )
    
    # Update user record
    db = await get_database()
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"avatar_path": file_path, "updated_at": datetime.utcnow()}}
    )
    
    return {"avatar_url": f"/static/avatars/{filename}"}

@router.get("/stats")
async def get_user_stats(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user statistics"""
    db = await get_database()
    
    # Count capsules
    total_capsules = await db.temporal_capsules.count_documents({"user_id": current_user.id})
    unlocked_capsules = await db.temporal_capsules.count_documents({
        "user_id": current_user.id,
        "status": "unlocked"
    })
    
    # Count friends
    friend_count = await db.friendships.count_documents({
        "$or": [
            {"requester_id": current_user.id, "status": "accepted"},
            {"addressee_id": current_user.id, "status": "accepted"}
        ]
    })
    
    # Count messages sent
    messages_sent = await db.chat_messages.count_documents({"sender_id": current_user.id})
    
    # Count quantum circuits
    circuits_created = await db.quantum_circuits.count_documents({"user_id": current_user.id})
    
    return {
        "total_capsules": total_capsules,
        "unlocked_capsules": unlocked_capsules,
        "locked_capsules": total_capsules - unlocked_capsules,
        "friend_count": friend_count,
        "messages_sent": messages_sent,
        "circuits_created": circuits_created,
        "quantum_level": current_user.quantum_level
    }

@router.get("/activity")
async def get_user_activity(
    limit: int = 20,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user's recent activity"""
    db = await get_database()
    
    activities = []
    
    # Recent capsules
    capsule_cursor = db.temporal_capsules.find({
        "user_id": current_user.id
    }).sort("created_at", -1).limit(5)
    
    async for capsule in capsule_cursor:
        activities.append({
            "type": "capsule_created",
            "description": f"Created capsule: {capsule['title']}",
            "timestamp": capsule["created_at"],
            "resource_id": str(capsule["_id"])
        })
    
    # Recent messages
    message_cursor = db.chat_messages.find({
        "sender_id": current_user.id
    }).sort("timestamp", -1).limit(5)
    
    async for message in message_cursor:
        activities.append({
            "type": "message_sent",
            "description": "Sent a quantum message",
            "timestamp": message["timestamp"],
            "resource_id": str(message["_id"])
        })
    
    # Sort by timestamp and limit
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"activities": activities[:limit]}
