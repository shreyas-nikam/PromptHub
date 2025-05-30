# app/core/rate_limiter.py
from fastapi import HTTPException, Request
from redis import asyncio as aioredis
from datetime import datetime, timedelta
from app.config import settings

class RateLimiter:
    def __init__(self):
        self.redis = None
    
    async def init(self):
        self.redis = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def check_rate_limit(self, key: str, limit: int = None) -> bool:
        """Check if request is within rate limit"""
        if not self.redis:
            await self.init()
        
        limit = limit or settings.rate_limit_per_minute
        now = datetime.now()
        window_start = now - timedelta(minutes=1)
        
        # Use Redis sorted set for sliding window
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start.timestamp())
        pipe.zadd(key, {str(now.timestamp()): now.timestamp()})
        pipe.zcount(key, window_start.timestamp(), now.timestamp())
        pipe.expire(key, 60)
        
        results = await pipe.execute()
        request_count = results[2]
        
        if request_count > limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {limit} requests per minute."
            )
        
        return True

rate_limiter = RateLimiter()

# Usage in dependencies
async def rate_limit_dependency(request: Request):
    client_ip = request.client.host
    await rate_limiter.check_rate_limit(f"rate_limit:{client_ip}")