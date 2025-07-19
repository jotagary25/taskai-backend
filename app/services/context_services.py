from typing import List, Dict, Any

import json

N_MAX_MESSAGES = 10
TTL_SECONDS = 60 * 60 * 6

class RedisContextService:
    def __init__(self, redis) -> None:
        self.redis = redis

    async def push_message(self, user_id: str, message: dict):
        key = f"context:user:{user_id}"
        await self.redis.lpush(key, json.dumps(message))
        await self.redis.ltrim(key, 0, N_MAX_MESSAGES - 1)
        await self.redis.expire(key, TTL_SECONDS)

    async def get_context(self, user_id: str) -> List[dict]:
        key = f"context:user:{user_id}"
        raw_messages = await self.redis.lrange(key, 0, N_MAX_MESSAGES - 1)
        return [json.loads(message) for message in reversed(raw_messages)]