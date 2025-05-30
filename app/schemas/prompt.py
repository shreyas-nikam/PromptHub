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