"""
services/cache_service.py
Redis AI response cache.
Key = SHA256(endpoint + sorted JSON of inputs), TTL = 15 minutes.
"""

import os
import json
import hashlib
import logging
import redis

logger = logging.getLogger("ai-service.cache")

_redis_client: redis.Redis | None = None
CACHE_TTL_SECONDS = 15 * 60  # 15 minutes


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(url, decode_responses=True)
    return _redis_client


def _make_key(endpoint: str, payload: dict) -> str:
    raw = endpoint + ":" + json.dumps(payload, sort_keys=True)
    return "ai_cache:" + hashlib.sha256(raw.encode()).hexdigest()


def cache_get(endpoint: str, payload: dict) -> dict | None:
    key = _make_key(endpoint, payload)
    try:
        value = _get_redis().get(key)
        if value:
            logger.info(f"Cache HIT for {endpoint}")
            return json.loads(value)
    except Exception as e:
        logger.warning(f"Redis cache_get error: {e}")
    return None


def cache_set(endpoint: str, payload: dict, result: dict) -> None:
    key = _make_key(endpoint, payload)
    try:
        _get_redis().setex(key, CACHE_TTL_SECONDS, json.dumps(result))
        logger.info(f"Cache SET for {endpoint} (TTL={CACHE_TTL_SECONDS}s)")
    except Exception as e:
        logger.warning(f"Redis cache_set error: {e}")
