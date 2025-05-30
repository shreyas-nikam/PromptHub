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

# app/models/prompt.py
from beanie import Document, Indexed, Link
from pydantic import Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

class Prompt(Document):
    prompt_id: Indexed(str)  # Human-readable ID
    name: str
    description: Optional[str] = None
    application_id: Optional[ObjectId] = None
    created_by: Optional[ObjectId] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    current_version: Optional[str] = None
    tags: List[str] = []
    
    class Settings:
        name = "prompts"
        indexes = [
            [("prompt_id", 1), ("application_id", 1)]  # Compound unique index
        ]

class PromptVersion(Document):
    prompt_id: ObjectId  # Reference to Prompt
    version: str  # Semantic versioning
    content: str
    system_prompt: Optional[str] = None
    metaprompt: Optional[str] = None
    required_fields: List[Dict[str, Any]] = []
    model_params: Dict[str, Any] = Field(default_factory=dict)
    guardrail_config: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None  # Vector embedding
    is_published: bool = False
    created_by: Optional[ObjectId] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Settings:
        name = "prompt_versions"
        indexes = [
            [("prompt_id", 1), ("version", 1)],  # Compound unique index
            "embedding"  # Vector search index
        ]