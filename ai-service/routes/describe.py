"""
routes/describe.py
POST /describe — analyse a risk record, return structured JSON description.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, request, jsonify

from services.sanitiser import sanitise_dict
from services.groq_client import call_groq
from services.cache_service import cache_get, cache_set
from services.chroma_service import query_knowledge

logger = logging.getLogger("ai-service.describe")
describe_bp = Blueprint("describe", __name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "describe_prompt.txt"
REQUIRED_FIELDS = ["risk_name", "category", "description", "likelihood", "impact", "existing_controls"]

FALLBACK_RESPONSE = {
    "risk_name": "Unknown",
    "category": "Unknown",
    "residual_score": 0,
    "risk_level": "UNKNOWN",
    "plain_english_summary": "AI service is temporarily unavailable. Please retry shortly.",
    "likelihood_explanation": "N/A",
    "impact_explanation": "N/A",
    "control_assessment": "N/A",
    "key_drivers": [],
    "is_fallback": True,
}


def _score_to_level(score: float) -> str:
    if score <= 6:
        return "LOW"
    elif score <= 12:
        return "MEDIUM"
    elif score <= 19:
        return "HIGH"
    return "CRITICAL"


@describe_bp.route("/describe", methods=["POST"])
def describe():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    # Validate required fields
    missing = [f for f in REQUIRED_FIELDS if not body.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    # Validate numeric ranges
    try:
        likelihood = int(body["likelihood"])
        impact = int(body["impact"])
        if not (1 <= likelihood <= 5) or not (1 <= impact <= 5):
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "likelihood and impact must be integers between 1 and 5"}), 400

    # Sanitise text fields
    text_fields = ["risk_name", "category", "description", "existing_controls"]
    try:
        sanitised, injection_detected = sanitise_dict(body, text_fields)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if injection_detected:
        return jsonify({"error": "Invalid input detected"}), 400

    residual_score = likelihood * impact
    sanitised["likelihood"] = likelihood
    sanitised["impact"] = impact
    sanitised["residual_score"] = residual_score

    # Check cache
    cache_key_payload = {k: sanitised[k] for k in REQUIRED_FIELDS + ["residual_score"]}
    cached = cache_get("describe", cache_key_payload)
    if cached:
        return jsonify(cached), 200

    # Load prompt template
    try:
        prompt_template = PROMPT_PATH.read_text()
    except FileNotFoundError:
        logger.error("Describe prompt template not found")
        return jsonify({**FALLBACK_RESPONSE, "generated_at": _now()}), 200

    # Fetch context from ChromaDB
    context_docs = query_knowledge(sanitised["description"] + " " + sanitised["risk_name"])
    context = "\n".join(context_docs) if context_docs else "No additional context available."

    # Fill prompt
    system_prompt = prompt_template.format(
        context=context,
        risk_name=sanitised["risk_name"],
        category=sanitised["category"],
        description=sanitised["description"],
        likelihood=likelihood,
        impact=impact,
        existing_controls=sanitised["existing_controls"],
        residual_score=residual_score,
    )

    # Call Groq
    raw = call_groq(system_prompt=system_prompt, user_message="Generate the risk description JSON now.", temperature=0.3)

    if raw is None:
        result = {**FALLBACK_RESPONSE, "risk_name": sanitised["risk_name"], "residual_score": residual_score,
                  "risk_level": _score_to_level(residual_score), "generated_at": _now()}
        return jsonify(result), 200

    try:
        result = json.loads(raw.strip())
        result["generated_at"] = _now()
        result.setdefault("is_fallback", False)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse Groq response as JSON: {e}\nRaw: {raw[:300]}")
        result = {**FALLBACK_RESPONSE, "risk_name": sanitised["risk_name"], "residual_score": residual_score,
                  "risk_level": _score_to_level(residual_score), "generated_at": _now()}
        return jsonify(result), 200

    cache_set("describe", cache_key_payload, result)
    return jsonify(result), 200


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
