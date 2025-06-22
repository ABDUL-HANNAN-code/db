import os
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/quantum_dashboard")
client = AsyncIOMotorClient(MONGODB_URL)
db = client.get_default_database()

@app.get("/api/health")
async def health_check():
    try:
        await client.admin.command("ping")
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}

@app.get("/api/users")
async def list_users():
    users = await db["users"].find().to_list(length=100)
    for user in users:
        user["_id"] = str(user["_id"])
    return {"users": users}
