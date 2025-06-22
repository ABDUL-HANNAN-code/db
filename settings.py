from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.models.settings import UserSetting
from app.routers.auth import get_current_user
from app.models.user import UserResponse
from app.database import get_database
from bson import ObjectId
from datetime import datetime
from pydantic import BaseSettings
import ast

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/")
async def get_settings(current_user: UserResponse = Depends(get_current_user)):
    db = await get_database()
    settings = {}
    async for s in db.configuration_settings.find({"user_id": current_user.id}):
        settings[s["setting_key"]] = s["setting_value"]
    return settings

@router.post("/")
async def update_setting(
    key: str, value: Any,
    current_user: UserResponse = Depends(get_current_user)
):
    db = await get_database()
    await db.configuration_settings.update_one(
        {"user_id": current_user.id, "setting_key": key},
        {"$set": {"setting_value": value, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    return {"status": "updated"}
