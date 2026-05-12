"""
services/groq_client.py
Wraps the Groq API — 3-retry with exponential backoff, error logging,
fallback template on all failures.
"""

import os
import time
import logging
from groq import Groq, RateLimitError, APIStatusError, APIConnectionError

logger = logging.getLogger("ai-service.groq")

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY is not set in environment")
        _client = Groq(api_key=api_key)
    return _client


def call_groq(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.3,
    max_tokens: int = 1000,
    max_retries: int = 3,
) -> str | None:
    """
    Call Groq LLaMA-3.3-70b with retry + exponential backoff.
    Returns the response text, or None on unrecoverable failure.
    """
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    client = _get_client()

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Groq call attempt {attempt}/{max_retries}, model={model}")
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            content = response.choices[0].message.content
            logger.info("Groq call succeeded")
            return content

        except RateLimitError as e:
            wait = 2 ** attempt
            logger.warning(f"Groq rate limit hit (attempt {attempt}). Waiting {wait}s. {e}")
            time.sleep(wait)

        except APIConnectionError as e:
            wait = 2 ** attempt
            logger.warning(f"Groq connection error (attempt {attempt}). Waiting {wait}s. {e}")
            time.sleep(wait)

        except APIStatusError as e:
            logger.error(f"Groq API status error (attempt {attempt}): status={e.status_code} — {e.message}")
            if e.status_code in (400, 401, 403):
                # Non-retryable
                break
            wait = 2 ** attempt
            time.sleep(wait)

        except Exception as e:
            logger.error(f"Unexpected error calling Groq (attempt {attempt}): {e}")
            time.sleep(2 ** attempt)

    logger.error("All Groq retry attempts exhausted — returning None")
    return None
