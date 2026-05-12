"""
services/chroma_service.py
In-memory vector knowledge store — no ChromaDB dependency.
Uses simple cosine similarity to find relevant domain knowledge.
Seeded with 10 domain knowledge documents on startup.
"""

import os
import math
import logging
from collections import Counter

logger = logging.getLogger("ai-service.chroma")

DOMAIN_DOCUMENTS = [
    "Residual risk is the remaining risk after all risk treatment measures have been applied. "
    "It represents the risk that an organisation accepts after implementing controls.",

    "Risk likelihood is assessed on a scale: 1 (Rare), 2 (Unlikely), 3 (Possible), "
    "4 (Likely), 5 (Almost Certain). Each level reflects probability of occurrence within a year.",

    "Risk impact is assessed on a scale: 1 (Insignificant), 2 (Minor), 3 (Moderate), "
    "4 (Major), 5 (Catastrophic). Impact covers financial, reputational, operational, and legal dimensions.",

    "Residual risk score = Likelihood x Impact after controls. "
    "Scores 1-6 are LOW, 7-12 are MEDIUM, 13-19 are HIGH, 20-25 are CRITICAL.",

    "ISO 31000 recommends that residual risks above the organisation's risk appetite "
    "must be escalated to senior management and treated with additional controls.",

    "Common risk treatment options: Avoid (eliminate the activity), Reduce (implement controls), "
    "Transfer (insurance, contracts), Accept (document and monitor). Each must be documented.",

    "Control effectiveness rating: 1 (Not effective), 2 (Partially effective), "
    "3 (Mostly effective), 4 (Fully effective). Controls must be tested periodically.",

    "Cybersecurity residual risks often include unpatched vulnerabilities, insider threats, "
    "and supply-chain risks. Multi-factor authentication and least-privilege reduce inherent risk significantly.",

    "Operational residual risks include process failures, key-person dependencies, and equipment failure. "
    "Business continuity plans and cross-training are primary mitigations.",

    "Regulatory and compliance residual risks arise when controls meet the letter but not the spirit "
    "of regulation. Regular internal audits and legal reviews are recommended treatments.",
]

_initialized = False


def _tokenize(text: str) -> list:
    return text.lower().split()


def _tf(tokens: list) -> dict:
    counts = Counter(tokens)
    total = len(tokens)
    return {word: count / total for word, count in counts.items()}


def _cosine_similarity(vec_a: dict, vec_b: dict) -> float:
    keys = set(vec_a) & set(vec_b)
    dot = sum(vec_a[k] * vec_b[k] for k in keys)
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def init_chroma() -> None:
    """Initialise in-memory knowledge store — no external dependencies."""
    global _initialized
    logger.info("Initialising in-memory knowledge store with 10 domain documents...")
    _initialized = True
    logger.info("Knowledge store ready — 10 documents loaded")


def query_knowledge(query_text: str, n_results: int = 3) -> list:
    """Return top-n relevant knowledge snippets using cosine similarity."""
    if not _initialized:
        return []
    try:
        query_vec = _tf(_tokenize(query_text))
        scored = []
        for doc in DOMAIN_DOCUMENTS:
            doc_vec = _tf(_tokenize(doc))
            score = _cosine_similarity(query_vec, doc_vec)
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:n_results]]
    except Exception as e:
        logger.warning(f"Knowledge query failed: {e}")
        return []
