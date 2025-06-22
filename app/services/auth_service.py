from app.models.user import User, UserCreate, UserResponse
from app.utils.security import get_password_hash, verify_password
from app.database import get_database
from datetime import datetime
from typing import Optional
from bson import ObjectId
import logging
import traceback

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.collection_name = "users"

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        db = await get_database()
        try:
            existing_user = await db[self.collection_name].find_one({
                "$or": [
                    {"email": user_data.email},
                    {"username": user_data.username}
                ]
            })
            if existing_user:
                raise ValueError("User already exists")

            hashed_password = get_password_hash(user_data.password)
            user_dict = {
                "username": user_data.username,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "hashed_password": hashed_password,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "quantum_level": 1,
                "total_capsules": 0,
                "unlocked_capsules": 0,
                "quantum_connections": []
            }
            result = await db[self.collection_name].insert_one(user_dict)
            return UserResponse(
                id=str(result.inserted_id),
                username=user_dict["username"],
                email=user_dict["email"],
                full_name=user_dict.get("full_name"),
                is_active=user_dict["is_active"],
                quantum_level=user_dict["quantum_level"],
                total_capsules=user_dict["total_capsules"],
                unlocked_capsules=user_dict["unlocked_capsules"]
            )
        except Exception:
            logger.error(traceback.format_exc())
            raise ValueError("Failed to create user")

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        db = await get_database()
        try:
            user = await db[self.collection_name].find_one({
                "$or": [
                    {"username": username},
                    {"email": username}
                ]
            })
            if not user or not verify_password(password, user["hashed_password"]):
                return None
            user["id"] = str(user["_id"])
            return User(**user)
        except Exception:
            logger.error(traceback.format_exc())
            return None

    async def get_current_user(self, user_id: str) -> Optional[UserResponse]:
        db = await get_database()
        try:
            user = await db[self.collection_name].find_one({"_id": ObjectId(user_id)})
            if user:
                return UserResponse(
                    id=str(user["_id"]),
                    username=user["username"],
                    email=user["email"],
                    full_name=user.get("full_name"),
                    is_active=user["is_active"],
                    quantum_level=user["quantum_level"],
                    total_capsules=user["total_capsules"],
                    unlocked_capsules=user["unlocked_capsules"]
                )
            return None
        except Exception:
            logger.error(traceback.format_exc())
            return None
