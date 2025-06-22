import os
from fastapi import FastAPI
from .database import get_database
from .routers import (
    auth,
    capsules,
    chat,
    friends,
    notifications,
    quantum,
    settings,
    users,
    vault,
    websocket,
)

app = FastAPI()

# Register API routers under the /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(capsules.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(friends.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(quantum.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(vault.router, prefix="/api")
app.include_router(websocket.router, prefix="/api")

@app.get("/api/health")
async def health_check():
    try:
        db = await get_database()
        await db.client.admin.command("ping")
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}

@app.get("/api/users")
async def list_users():
    db = await get_database()
    users = await db["users"].find().to_list(length=100)
    for user in users:
        user["_id"] = str(user["_id"])
    return {"users": users}
