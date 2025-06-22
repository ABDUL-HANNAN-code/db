import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

_client: Optional[AsyncIOMotorClient] = None


def _get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/quantum_dashboard")
        _client = AsyncIOMotorClient(mongodb_url)
    return _client


async def get_database():
    """Return the application's MongoDB database instance."""
    client = _get_client()
    db_name = os.getenv("DATABASE_NAME")
    return client[db_name] if db_name else client.get_default_database()
