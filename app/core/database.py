from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

client: AsyncIOMotorClient | None = None


async def connect_db() -> None:
    global client
    client = AsyncIOMotorClient(settings.MONGODB_URL)


async def close_db() -> None:
    if client:
        client.close()


def get_db() -> AsyncIOMotorDatabase:
    if client is None:
        raise RuntimeError("Database client is not initialized.")
    return client[settings.DATABASE_NAME]
