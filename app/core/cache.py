# app/core/cache.py
from redis import asyncio as aioredis
from typing import Optional, Any
import json
from datetime import timedelta
from app.config import settings

class CacheManager:
    def __init__(self):
        self.redis = None
    
    async def init(self):
        self.redis = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis:
            await self.init()
        
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[timedelta] = None
    ):
        """Set value in cache"""
        if not self.redis:
            await self.init()
        
        serialized = json.dumps(value)
        if expire:
            await self.redis.set(key, serialized, ex=int(expire.total_seconds()))
        else:
            await self.redis.set(key, serialized)
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.redis:
            await self.init()
        
        await self.redis.delete(key)
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        if not self.redis:
            await self.init()
        
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

cache_manager = CacheManager()

# Usage example in prompt service
async def get_prompt_cached(prompt_id: str, version: str):
    cache_key = f"prompt:{prompt_id}:{version}"
    
    # Try cache first
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    # Get from database
    prompt = await get_prompt_from_db(prompt_id, version)
    
    # Cache for 1 hour
    await cache_manager.set(cache_key, prompt, expire=timedelta(hours=1))
    
    return prompt