"""
routes/health.py
GET /health — service health status, model info, uptime, avg response time.
"""

import os
import time
import logging
from datetime import datetime, timezone
from collections import deque

from flask import Blueprint, jsonify

logger = logging.getLogger("ai-service.health")
health_bp = Blueprint("health", __name__)

# Rolling window of last 50 response times (seconds)
_response_times: deque = deque(maxlen=50)


def record_response_time(seconds: float) -> None:
    """Called by route handlers to record Groq response times."""
    _response_times.append(seconds)


@health_bp.route("/health", methods=["GET"])
def health():
    from app import APP_START_TIME

    uptime_seconds = int(time.time() - APP_START_TIME)
    uptime_str = _format_uptime(uptime_seconds)

    avg_response_ms = (
        round(sum(_response_times) / len(_response_times) * 1000, 1)
        if _response_times else None
    )

    # Check Redis connectivity
    redis_status = "ok"
    try:
        import redis as r
        client = r.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        client.ping()
    except Exception:
        redis_status = "unavailable"

    # Check knowledge store
    chroma_status = "ok"
    try:
        from services.chroma_service import _initialized
        if not _initialized:
            chroma_status = "unavailable"
    except Exception:
        chroma_status = "unavailable"

    result = {
        "status": "ok",
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "uptime": uptime_str,
        "uptime_seconds": uptime_seconds,
        "avg_response_time_ms": avg_response_ms,
        "sample_count": len(_response_times),
        "dependencies": {
            "redis": redis_status,
            "chromadb": chroma_status,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return jsonify(result), 200


def _format_uptime(seconds: int) -> str:
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if mins:
        parts.append(f"{mins}m")
    parts.append(f"{secs}s")
    return " ".join(parts)
