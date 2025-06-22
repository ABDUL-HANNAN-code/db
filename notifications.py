from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models.notification import Notification
from app.routers.auth import get_current_user
from app.models.user import UserResponse
from app.database import get_database
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/", response_model=List[Notification])
async def get_notifications(current_user: UserResponse = Depends(get_current_user)):
    db = await get_database()
    notifications = []
    async for n in db.system_notifications.find({"user_id": current_user.id}).sort("created_at", -1):
        n["id"] = str(n["_id"])
        notifications.append(Notification(**n))
    return notifications

@router.post("/{notification_id}/read")
async def mark_read(notification_id: str, current_user: UserResponse = Depends(get_current_user)):
    db = await get_database()
    result = await db.system_notifications.update_one(
        {"_id": ObjectId(notification_id), "user_id": current_user.id},
        {"$set": {"read": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "read"}
