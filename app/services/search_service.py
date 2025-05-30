# app/services/search_service.py
from typing import List, Dict, Any, Optional
from bson import ObjectId
from app.models.prompt import PromptVersion
from app.utils.embeddings import EmbeddingService

class SearchService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        application_id: Optional[str] = None
    ) -> List[PromptVersion]:
        """
        Perform semantic search using MongoDB Atlas Vector Search
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        # MongoDB Atlas Vector Search aggregation pipeline
        pipeline = [
            {
                "$search": {
                    "index": "vector_index",
                    "knnBeta": {
                        "vector": query_embedding,
                        "path": "embedding",
                        "k": limit
                    }
                }
            },
            {
                "$project": {
                    "score": {"$meta": "searchScore"},
                    "content": 1,
                    "version": 1,
                    "prompt_id": 1,
                    "system_prompt": 1,
                    "required_fields": 1
                }
            }
        ]
        
        # Add application filter if provided
        if application_id:
            pipeline.insert(1, {
                "$match": {"application_id": ObjectId(application_id)}
            })
        
        results = await PromptVersion.aggregate(pipeline).to_list()
        
        return results