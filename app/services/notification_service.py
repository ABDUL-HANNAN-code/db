from app.models.notification import Notification
from app.database import get_database
from datetime import datetime
from bson import ObjectId

class NotificationService:
    def __init__(self):
        self.collection = "system_notifications"

    async def send_notification(self, user_id: str, notification_type: str, title: str, message: str):
        db = await get_database()
        notification = {
            "user_id": user_id,
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "read": False,
            "created_at": datetime.utcnow()
        }
        result = await db[self.collection].insert_one(notification)
        notification["id"] = str(result.inserted_id)
        return Notification(**notification)

notification_service = NotificationService()
