# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional
import os

from app.models.user import User
from app.models.prompt import Prompt, PromptVersion
from app.models.execution import ExecutionLog
from app.models.feedback import Feedback
from app.models.application import Application
from app.models.prompt_source import PromptSource

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None

db = MongoDB()

async def connect_to_mongodb():
    """Create database connection"""
    db.client = AsyncIOMotorClient(
        os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
        maxPoolSize=10,
        minPoolSize=1
    )
    
    # Initialize Beanie with document models
    await init_beanie(
        database=db.client[os.getenv("MONGODB_DB_NAME", "prompthub")],
        document_models=[
            User,
            Application,
            Prompt,
            PromptVersion,
            ExecutionLog,
            Feedback,
            PromptSource
        ]
    )

async def close_mongodb_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
