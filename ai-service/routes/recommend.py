"""
routes/recommend.py
POST /recommend — return 3 actionable risk treatment recommendations.
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

logger = logging.getLogger("ai-service.recommend")
recommend_bp = Blueprint("recommend", __name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "recommend_prompt.txt"
REQUIRED_FIELDS = ["risk_name", "category", "description", "likelihood", "impact", "existing_controls"]

FALLBACK_RESPONSE = {
    "risk_name": "Unknown",
    "recommendations": [
        {
            "action_type": "Reduce",
            "description": "AI service is temporarily unavailable. Please consult your risk register manually for treatment options.",
            "priority": "HIGH",
            "estimated_risk_reduction": "N/A",
            "implementation_effort": "N/A",
        }
    ],
    "is_fallback": True,
}


def _score_to_level(score: int) -> str:
    if score <= 6:
        return "LOW"
    elif score <= 12:
        return "MEDIUM"
    elif score <= 19:
        return "HIGH"
    return "CRITICAL"


@recommend_bp.route("/recommend", methods=["POST"])
def recommend():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    missing = [f for f in REQUIRED_FIELDS if not body.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    try:
        likelihood = int(body["likelihood"])
        impact = int(body["impact"])
        if not (1 <= likelihood <= 5) or not (1 <= impact <= 5):
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "likelihood and impact must be integers between 1 and 5"}), 400

    text_fields = ["risk_name", "category", "description", "existing_controls"]
    try:
        sanitised, injection_detected = sanitise_dict(body, text_fields)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if injection_detected:
        return jsonify({"error": "Invalid input detected"}), 400

    residual_score = likelihood * impact
    risk_level = _score_to_level(residual_score)

    cache_key_payload = {k: sanitised.get(k) for k in REQUIRED_FIELDS}
    cache_key_payload.update({"likelihood": likelihood, "impact": impact})
    cached = cache_get("recommend", cache_key_payload)
    if cached:
        return jsonify(cached), 200

    try:
        prompt_template = PROMPT_PATH.read_text()
    except FileNotFoundError:
        logger.error("Recommend prompt template not found")
        return jsonify({**FALLBACK_RESPONSE, "risk_name": sanitised["risk_name"], "generated_at": _now()}), 200

    context_docs = query_knowledge(sanitised["description"] + " treatment " + sanitised["category"])
    context = "\n".join(context_docs) if context_docs else "No additional context available."

    system_prompt = prompt_template.format(
        context=context,
        risk_name=sanitised["risk_name"],
        category=sanitised["category"],
        description=sanitised["description"],
        likelihood=likelihood,
        impact=impact,
        existing_controls=sanitised["existing_controls"],
        residual_score=residual_score,
        risk_level=risk_level,
    )

    raw = call_groq(system_prompt=system_prompt, user_message="Generate the 3 recommendations JSON now.", temperature=0.4)

    if raw is None:
        result = {**FALLBACK_RESPONSE, "risk_name": sanitised["risk_name"], "generated_at": _now()}
        return jsonify(result), 200

    try:
        result = json.loads(raw.strip())
        result["generated_at"] = _now()
        result.setdefault("is_fallback", False)

        # Enforce exactly 3 recommendations
        recs = result.get("recommendations", [])
        if len(recs) != 3:
            logger.warning(f"Expected 3 recommendations, got {len(recs)}")

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse Groq response as JSON: {e}\nRaw: {raw[:300]}")
        result = {**FALLBACK_RESPONSE, "risk_name": sanitised["risk_name"], "generated_at": _now()}
        return jsonify(result), 200

    cache_set("recommend", cache_key_payload, result)
    return jsonify(result), 200


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
