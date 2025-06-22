from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.database import get_database
from app.routers.auth import get_current_user
from app.models.user import UserResponse
from app.services.permission_service import permission_service
from bson import ObjectId
from datetime import datetime, timedelta

router = APIRouter(prefix="/vault", tags=["quantum-vault"])

@router.get("/items")
async def get_vault_items(
    category: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get items from quantum vault"""
    db = await get_database()
    
    # Build query
    query = {"user_id": current_user.id}
    if category:
        query["item_type"] = category
    
    # Get vault items
    vault_items = []
    cursor = db.quantum_vault_items.find(query).sort("created_at", -1).skip(offset).limit(limit)
    
    async for item in cursor:
        vault_items.append({
            "id": str(item["_id"]),
            "item_type": item["item_type"],
            "item_data": item["item_data"],
            "access_permissions": item["access_permissions"],
            "created_at": item["created_at"]
        })
    
    return {"vault_items": vault_items}

@router.post("/items")
async def store_vault_item(
    item_type: str,
    item_data: dict,
    access_permissions: List[str] = [],
    current_user: UserResponse = Depends(get_current_user)
):
    """Store item in quantum vault"""
    db = await get_database()
    
    vault_item = {
        "user_id": current_user.id,
        "item_type": item_type,
        "item_data": item_data,
        "access_permissions": access_permissions,
        "created_at": datetime.utcnow()
    }
    
    result = await db.quantum_vault_items.insert_one(vault_item)
    vault_item["id"] = str(result.inserted_id)
    
    return vault_item

@router.get("/analytics")
async def get_vault_analytics(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get vault analytics and insights"""
    db = await get_database()
    
    # Count items by type
    pipeline = [
        {"$match": {"user_id": current_user.id}},
        {"$group": {
            "_id": "$item_type",
            "count": {"$sum": 1}
        }}
    ]
    
    type_counts = {}
    async for result in db.quantum_vault_items.aggregate(pipeline):
        type_counts[result["_id"]] = result["count"]
    
    # Recent activity
    recent_items = await db.quantum_vault_items.count_documents({
        "user_id": current_user.id,
        "created_at": {"$gte": datetime.utcnow() - timedelta(days=30)}
    })
    
    return {
        "total_items": sum(type_counts.values()),
        "items_by_type": type_counts,
        "recent_activity": recent_items
    }

@router.delete("/items/{item_id}")
async def delete_vault_item(
    item_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete item from vault"""
    db = await get_database()
    
    result = await db.quantum_vault_items.delete_one({
        "_id": ObjectId(item_id),
        "user_id": current_user.id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vault item not found"
        )
    
    return {"status": "deleted"}
