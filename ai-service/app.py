"""
Tool-114 — Residual Risk Calculator
AI Microservice — Flask 3.x on port 5000
AI Developer 1
"""

import os
import time
import logging
from dotenv import load_dotenv
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("ai-service")

# ── App startup time (for /health uptime) ────────────────────────────────────
APP_START_TIME = time.time()

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

# ── Rate limiter — 30 req/min per IP ─────────────────────────────────────────
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["30 per minute"],
    storage_uri=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

# ── Security headers on every response ───────────────────────────────────────
@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'none'"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response

# ── Register blueprints ───────────────────────────────────────────────────────
from routes.describe import describe_bp
from routes.recommend import recommend_bp
from routes.report import report_bp
from routes.health import health_bp

app.register_blueprint(describe_bp)
app.register_blueprint(recommend_bp)
app.register_blueprint(report_bp)
app.register_blueprint(health_bp)

# ── Pre-load sentence-transformers at startup ─────────────────────────────────
from services.chroma_service import init_chroma
init_chroma()

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("AI_PORT", 5000))
    debug = os.getenv("FLASK_ENV", "production") == "development"
    logger.info(f"Starting AI service on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)
