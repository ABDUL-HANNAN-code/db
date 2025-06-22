from app.models.settings import UserSetting
from app.database import get_database
from datetime import datetime

class SettingsService:
    def __init__(self):
        self.collection = "configuration_settings"

    async def get_settings(self, user_id: str):
        db = await get_database()
        settings = {}
        async for s in db[self.collection].find({"user_id": user_id}):
            settings[s["setting_key"]] = s["setting_value"]
        return settings

    async def update_setting(self, user_id: str, key: str, value):
        db = await get_database()
        await db[self.collection].update_one(
            {"user_id": user_id, "setting_key": key},
            {"$set": {"setting_value": value, "updated_at": datetime.utcnow()}},
            upsert=True
        )
        return True

settings_service = SettingsService()
