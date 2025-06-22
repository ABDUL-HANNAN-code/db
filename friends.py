from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.models.friendship import Friendship, FriendRequest, UserProfile, FriendshipStatus
from app.database import get_database
from app.routers.auth import get_current_user
from app.models.user import UserResponse
from app.services.connection_manager import connection_manager
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/friends", tags=["friends"])

@router.post("/request")
async def send_friend_request(
    friend_request: FriendRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Send a friend request"""
    db = await get_database()
    
    # Find target user
    target_user = await db.users.find_one({"username": friend_request.addressee_username})
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    target_user_id = str(target_user["_id"])
    
    # Check if friendship already exists
    existing_friendship = await db.friendships.find_one({
        "$or": [
            {"requester_id": current_user.id, "addressee_id": target_user_id},
            {"requester_id": target_user_id, "addressee_id": current_user.id}
        ]
    })
    
    if existing_friendship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Friendship request already exists or users are already friends"
        )
    
    # Create friendship request
    friendship_data = {
        "requester_id": current_user.id,
        "addressee_id": target_user_id,
        "status": FriendshipStatus.PENDING,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.friendships.insert_one(friendship_data)
    friendship_data["id"] = str(result.inserted_id)
    
    # Send real-time notification
    notification = {
        "type": "friend_request",
        "requester": {
            "id": current_user.id,
            "username": current_user.username,
            "full_name": current_user.full_name
        },
        "message": friend_request.message,
        "friendship_id": friendship_data["id"],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await connection_manager.send_personal_message(target_user_id, notification)
    
    return Friendship(**friendship_data)

@router.post("/respond/{friendship_id}")
async def respond_to_friend_request(
    friendship_id: str,
    accept: bool,
    current_user: UserResponse = Depends(get_current_user)
):
    """Accept or decline a friend request"""
    db = await get_database()
    
    # Find friendship request
    friendship = await db.friendships.find_one({
        "_id": ObjectId(friendship_id),
        "addressee_id": current_user.id,
        "status": FriendshipStatus.PENDING
    })
    
    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend request not found"
        )
    
    new_status = FriendshipStatus.ACCEPTED if accept else FriendshipStatus.BLOCKED
    
    # Update friendship status
    await db.friendships.update_one(
        {"_id": ObjectId(friendship_id)},
        {
            "$set": {
                "status": new_status,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Send notification to requester
    notification = {
        "type": "friend_request_response",
        "accepted": accept,
        "responder": {
            "id": current_user.id,
            "username": current_user.username,
            "full_name": current_user.full_name
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await connection_manager.send_personal_message(friendship["requester_id"], notification)
    
    return {"status": "accepted" if accept else "declined"}

@router.get("/", response_model=List[UserProfile])
async def get_friends(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user's friends list"""
    db = await get_database()
    
    friends = []
    
    # Find accepted friendships
    cursor = db.friendships.find({
        "$or": [
            {"requester_id": current_user.id, "status": FriendshipStatus.ACCEPTED},
            {"addressee_id": current_user.id, "status": FriendshipStatus.ACCEPTED}
        ]
    })
    
    async for friendship in cursor:
        # Determine friend's ID
        friend_id = (friendship["addressee_id"] 
                    if friendship["requester_id"] == current_user.id 
                    else friendship["requester_id"])
        
        # Get friend's details
        friend = await db.users.find_one({"_id": ObjectId(friend_id)})
        if friend:
            # Check online status
            is_online = await connection_manager.is_user_online(friend_id)
            
            friend_profile = UserProfile(
                id=str(friend["_id"]),
                username=friend["username"],
                full_name=friend.get("full_name"),
                quantum_level=friend.get("quantum_level", 1),
                is_online=is_online,
                last_seen=friend.get("last_login")
            )
            friends.append(friend_profile)
    
    return friends

@router.get("/requests")
async def get_friend_requests(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get pending friend requests"""
    db = await get_database()
    
    requests = []
    
    # Get incoming requests
    incoming_cursor = db.friendships.find({
        "addressee_id": current_user.id,
        "status": FriendshipStatus.PENDING
    })
    
    async for request in incoming_cursor:
        requester = await db.users.find_one({"_id": ObjectId(request["requester_id"])})
        if requester:
            requests.append({
                "id": str(request["_id"]),
                "type": "incoming",
                "user": {
                    "id": str(requester["_id"]),
                    "username": requester["username"],
                    "full_name": requester.get("full_name")
                },
                "created_at": request["created_at"]
            })
    
    # Get sent requests
    outgoing_cursor = db.friendships.find({
        "requester_id": current_user.id,
        "status": FriendshipStatus.PENDING
    })
    
    async for request in outgoing_cursor:
        addressee = await db.users.find_one({"_id": ObjectId(request["addressee_id"])})
        if addressee:
            requests.append({
                "id": str(request["_id"]),
                "type": "outgoing",
                "user": {
                    "id": str(addressee["_id"]),
                    "username": addressee["username"],
                    "full_name": addressee.get("full_name")
                },
                "created_at": request["created_at"]
            })
    
    return {"friend_requests": requests}

@router.get("/search")
async def search_users(
    query: str = Query(..., min_length=2),
    current_user: UserResponse = Depends(get_current_user)
):
    """Search for users to befriend"""
    db = await get_database()
    
    # Search users by username or full name
    search_cursor = db.users.find({
        "$and": [
            {"_id": {"$ne": ObjectId(current_user.id)}},  # Exclude self
            {
                "$or": [
                    {"username": {"$regex": query, "$options": "i"}},
                    {"full_name": {"$regex": query, "$options": "i"}}
                ]
            }
        ]
    }).limit(20)
    
    users = []
    async for user in search_cursor:
        # Check friendship status
        friendship = await db.friendships.find_one({
            "$or": [
                {"requester_id": current_user.id, "addressee_id": str(user["_id"])},
                {"requester_id": str(user["_id"]), "addressee_id": current_user.id}
            ]
        })
        
        friendship_status = "none"
        if friendship:
            if friendship["status"] == FriendshipStatus.ACCEPTED:
                friendship_status = "friends"
            elif friendship["status"] == FriendshipStatus.PENDING:
                if friendship["requester_id"] == current_user.id:
                    friendship_status = "request_sent"
                else:
                    friendship_status = "request_received"
            elif friendship["status"] == FriendshipStatus.BLOCKED:
                friendship_status = "blocked"
        
        users.append({
            "id": str(user["_id"]),
            "username": user["username"],
            "full_name": user.get("full_name"),
            "quantum_level": user.get("quantum_level", 1),
            "friendship_status": friendship_status,
            "is_online": await connection_manager.is_user_online(str(user["_id"]))
        })
    
    return {"users": users}

@router.delete("/{friend_id}")
async def remove_friend(
    friend_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Remove a friend"""
    db = await get_database()
    
    result = await db.friendships.delete_one({
        "$or": [
            {"requester_id": current_user.id, "addressee_id": friend_id},
            {"requester_id": friend_id, "addressee_id": current_user.id}
        ],
        "status": FriendshipStatus.ACCEPTED
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friendship not found"
        )
    
    return {"status": "removed"}
