from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.capsule import TemporalCapsule, CapsuleCreate, CapsuleStatus
from app.models.user import UserResponse
from app.routers.auth import get_current_user
from app.database import get_database
from app.services.permission_service import permission_service
from app.models.permissions import ShareRequest
from bson import ObjectId

router = APIRouter(prefix="/capsules", tags=["temporal-capsules"])

@router.post("/", response_model=TemporalCapsule)
async def create_capsule(
    capsule_data: CapsuleCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new temporal capsule"""
    db = await get_database()
    
    capsule_dict = {
        "user_id": current_user.id,
        "title": capsule_data.title,
        "description": capsule_data.description,
        "capsule_type": capsule_data.capsule_type,
        "content": capsule_data.content,
        "unlock_date": capsule_data.unlock_date,
        "created_at": datetime.utcnow(),
        "status": CapsuleStatus.LOCKED,
        "access_count": 0,
        "tags": capsule_data.tags
    }
    
    result = await db.temporal_capsules.insert_one(capsule_dict)
    capsule_dict["id"] = str(result.inserted_id)
    
    # Update user capsule count
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$inc": {"total_capsules": 1}}
    )
    
    return TemporalCapsule(**capsule_dict)

@router.get("/", response_model=List[TemporalCapsule])
async def get_user_capsules(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all capsules created by the user"""
    db = await get_database()
    
    capsules = []
    cursor = db.temporal_capsules.find({"user_id": current_user.id})
    
    async for capsule in cursor:
        capsule["id"] = str(capsule["_id"])
        capsules.append(TemporalCapsule(**capsule))
    
    return capsules

@router.get("/unlockable")
async def get_unlockable_capsules(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get capsules that are ready to be unlocked"""
    db = await get_database()
    
    now = datetime.utcnow()
    capsules = []
    
    cursor = db.temporal_capsules.find({
        "user_id": current_user.id,
        "unlock_date": {"$lte": now},
        "status": CapsuleStatus.LOCKED
    })
    
    async for capsule in cursor:
        # Update status to unlocked
        await db.temporal_capsules.update_one(
            {"_id": capsule["_id"]},
            {"$set": {"status": CapsuleStatus.UNLOCKED}}
        )
        
        capsule["id"] = str(capsule["_id"])
        capsule["status"] = CapsuleStatus.UNLOCKED
        capsules.append(TemporalCapsule(**capsule))
    
    if capsules:
        # Update user unlocked capsules count
        await db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$inc": {"unlocked_capsules": len(capsules)}}
        )
    
    return capsules

@router.get("/{capsule_id}", response_model=TemporalCapsule)
async def get_capsule(
    capsule_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific capsule by ID"""
    db = await get_database()
    
    # First check if user owns the capsule
    capsule = await db.temporal_capsules.find_one({
        "_id": ObjectId(capsule_id),
        "user_id": current_user.id
    })
    
    # If not owned, check if it's shared with the user
    if not capsule:
        permission = await permission_service.check_capsule_permission(
            current_user.id, capsule_id
        )
        
        if permission:
            capsule = await db.temporal_capsules.find_one({
                "_id": ObjectId(capsule_id)
            })
        
        if not capsule or not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Capsule not found"
            )
    
    # Check if capsule can be accessed
    if capsule["status"] == CapsuleStatus.LOCKED and capsule["unlock_date"] > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Capsule is still locked"
        )
    
    # Increment access count
    await db.temporal_capsules.update_one(
        {"_id": ObjectId(capsule_id)},
        {"$inc": {"access_count": 1}}
    )
    
    capsule["id"] = str(capsule["_id"])
    return TemporalCapsule(**capsule)

@router.put("/{capsule_id}")
async def update_capsule(
    capsule_id: str,
    capsule_data: CapsuleCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update a capsule (only if it's still locked)"""
    db = await get_database()
    
    # Check if capsule exists and belongs to user
    capsule = await db.temporal_capsules.find_one({
        "_id": ObjectId(capsule_id),
        "user_id": current_user.id
    })
    
    if not capsule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capsule not found"
        )
    
    # Only allow updates if capsule is still locked
    if capsule["status"] != CapsuleStatus.LOCKED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update an unlocked capsule"
        )
    
    # Update capsule
    update_data = {
        "title": capsule_data.title,
        "description": capsule_data.description,
        "content": capsule_data.content,
        "unlock_date": capsule_data.unlock_date,
        "tags": capsule_data.tags
    }
    
    await db.temporal_capsules.update_one(
        {"_id": ObjectId(capsule_id)},
        {"$set": update_data}
    )
    
    return {"status": "updated"}

@router.delete("/{capsule_id}")
async def delete_capsule(
    capsule_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a capsule"""
    db = await get_database()
    
    # Check if capsule exists and belongs to user
    capsule = await db.temporal_capsules.find_one({
        "_id": ObjectId(capsule_id),
        "user_id": current_user.id
    })
    
    if not capsule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capsule not found"
        )
    
    # Delete capsule
    await db.temporal_capsules.delete_one({"_id": ObjectId(capsule_id)})
    
    # Update user capsule count
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$inc": {"total_capsules": -1}}
    )
    
    # If capsule was unlocked, also decrement unlocked count
    if capsule["status"] == CapsuleStatus.UNLOCKED:
        await db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$inc": {"unlocked_capsules": -1}}
        )
    
    return {"status": "deleted"}

@router.post("/{capsule_id}/share")
async def share_capsule(
    capsule_id: str,
    share_request: ShareRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Share a capsule with another user"""
    share_request.capsule_id = capsule_id
    try:
        permission = await permission_service.share_capsule(current_user.id, share_request)
        return {"status": "shared", "permission": permission.dict()}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/shared")
async def get_shared_capsules(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get capsules shared with the current user"""
    shared_capsules = await permission_service.get_shared_capsules(current_user.id)
    return {"shared_capsules": shared_capsules}

@router.get("/{capsule_id}/access")
async def check_capsule_access(
    capsule_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check user's access level to a capsule"""
    permission_level = await permission_service.check_capsule_permission(
        current_user.id, 
        capsule_id
    )
    
    if permission_level is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this capsule"
        )
    
    return {
        "capsule_id": capsule_id,
        "permission_level": permission_level,
        "has_access": True
    }

@router.delete("/{capsule_id}/share/{user_id}")
async def revoke_capsule_access(
    capsule_id: str,
    user_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Revoke capsule access from a user"""
    await permission_service.revoke_capsule_access(
        current_user.id,
        capsule_id,
        user_id
    )
    return {"status": "access_revoked"}
