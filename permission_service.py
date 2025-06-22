from app.models.permissions import CapsulePermission, PermissionLevel, ShareRequest
from app.database import get_database
from app.services.connection_manager import connection_manager
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List, Optional

class PermissionService:
    def __init__(self):
        self.collection_name = "capsule_permissions"
    
    async def share_capsule(self, owner_id: str, share_request: ShareRequest) -> CapsulePermission:
        """Share a capsule with another user"""
        db = await get_database()
        
        # Get the user to share with
        target_user = await db.users.find_one({"username": share_request.username})
        if not target_user:
            raise ValueError("User not found")
        
        target_user_id = str(target_user["_id"])
        
        # Verify capsule ownership
        capsule = await db.temporal_capsules.find_one({
            "_id": ObjectId(share_request.capsule_id),
            "user_id": owner_id
        })
        if not capsule:
            raise ValueError("Capsule not found or access denied")
        
        # Check if permission already exists
        existing_permission = await db[self.collection_name].find_one({
            "capsule_id": share_request.capsule_id,
            "shared_with_user_id": target_user_id
        })
        
        if existing_permission:
            # Update existing permission
            update_data = {
                "permission_level": share_request.permission_level,
                "updated_at": datetime.utcnow(),
                "is_active": True
            }
            
            if share_request.expires_in_days:
                update_data["expires_at"] = datetime.utcnow() + timedelta(days=share_request.expires_in_days)
            
            await db[self.collection_name].update_one(
                {"_id": existing_permission["_id"]},
                {"$set": update_data}
            )
            
            existing_permission.update(update_data)
            existing_permission["id"] = str(existing_permission["_id"])
            permission = CapsulePermission(**existing_permission)
        else:
            # Create new permission
            permission_data = {
                "capsule_id": share_request.capsule_id,
                "owner_id": owner_id,
                "shared_with_user_id": target_user_id,
                "permission_level": share_request.permission_level,
                "granted_at": datetime.utcnow(),
                "is_active": True
            }
            
            if share_request.expires_in_days:
                permission_data["expires_at"] = datetime.utcnow() + timedelta(days=share_request.expires_in_days)
            
            result = await db[self.collection_name].insert_one(permission_data)
            permission_data["id"] = str(result.inserted_id)
            permission = CapsulePermission(**permission_data)
        
        # Send real-time notification
        await self._notify_capsule_shared(permission, capsule, share_request.message)
        
        return permission
    
    async def get_shared_capsules(self, user_id: str) -> List[dict]:
        """Get capsules shared with the user"""
        db = await get_database()
        
        # Get active permissions for the user
        permissions_cursor = db[self.collection_name].find({
            "shared_with_user_id": user_id,
            "is_active": True,
            "$or": [
                {"expires_at": {"$exists": False}},
                {"expires_at": {"$gt": datetime.utcnow()}}
            ]
        })
        
        shared_capsules = []
        async for permission in permissions_cursor:
            # Get the capsule details
            capsule = await db.temporal_capsules.find_one({
                "_id": ObjectId(permission["capsule_id"])
            })
            
            if capsule:
                # Get owner details
                owner = await db.users.find_one({
                    "_id": ObjectId(permission["owner_id"])
                })
                
                capsule_data = {
                    "id": str(capsule["_id"]),
                    "title": capsule["title"],
                    "description": capsule.get("description"),
                    "capsule_type": capsule["capsule_type"],
                    "unlock_date": capsule["unlock_date"],
                    "created_at": capsule["created_at"],
                    "status": capsule["status"],
                    "owner": {
                        "id": str(owner["_id"]),
                        "username": owner["username"],
                        "full_name": owner.get("full_name")
                    },
                    "permission_level": permission["permission_level"],
                    "shared_at": permission["granted_at"]
                }
                
                # Only include content if user has appropriate permissions and capsule is unlocked
                if (permission["permission_level"] in ["view", "comment", "interact"] and 
                    capsule["status"] == "unlocked"):
                    capsule_data["content"] = capsule["content"]
                
                shared_capsules.append(capsule_data)
        
        return shared_capsules
    
    async def check_capsule_permission(self, user_id: str, capsule_id: str) -> Optional[PermissionLevel]:
        """Check user's permission level for a capsule"""
        db = await get_database()
        
        # Check if user owns the capsule
        capsule = await db.temporal_capsules.find_one({
            "_id": ObjectId(capsule_id),
            "user_id": user_id
        })
        if capsule:
            return PermissionLevel.INTERACT  # Owner has full access
        
        # Check shared permissions
        permission = await db[self.collection_name].find_one({
            "capsule_id": capsule_id,
            "shared_with_user_id": user_id,
            "is_active": True,
            "$or": [
                {"expires_at": {"$exists": False}},
                {"expires_at": {"$gt": datetime.utcnow()}}
            ]
        })
        
        if permission:
            return PermissionLevel(permission["permission_level"])
        
        return None
    
    async def revoke_capsule_access(self, owner_id: str, capsule_id: str, user_id: str):
        """Revoke capsule access from a user"""
        db = await get_database()
        
        await db[self.collection_name].update_one(
            {
                "capsule_id": capsule_id,
                "owner_id": owner_id,
                "shared_with_user_id": user_id
            },
            {"$set": {"is_active": False}}
        )
    
    async def _notify_capsule_shared(self, permission: CapsulePermission, capsule: dict, message: Optional[str]):
        """Send notification about shared capsule"""
        notification_data = {
            "type": "capsule_shared",
            "capsule": {
                "id": permission.capsule_id,
                "title": capsule["title"],
                "permission_level": permission.permission_level
            },
            "owner_id": permission.owner_id,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await connection_manager.send_personal_message(
            permission.shared_with_user_id,
            notification_data
        )

permission_service = PermissionService()
