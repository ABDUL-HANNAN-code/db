import os
from fastapi import FastAPI
from .database import get_database

app = FastAPI()

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
