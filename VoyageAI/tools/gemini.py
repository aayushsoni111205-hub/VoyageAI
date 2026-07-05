"""
tools/gemini.py
----------------
Thin wrapper around Google's Gemini API. Every agent talks to Gemini through
this module only — no agent should import google.generativeai directly.
This keeps the SDK swappable (e.g. for testing or a future provider change)
and gives us one place to handle auth, retries, and error formatting.
"""

from __future__ import annotations

import os
import time
from typing import Optional

from dotenv import load_dotenv

from utils.constants import DEFAULT_GEMINI_MODEL
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

_MAX_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 2

_client = None  # lazily initialized google.genai client


class GeminiError(RuntimeError):
    """Raised when Gemini fails to produce a usable response."""


def _get_client():
    """Lazily create and cache the Gemini client using GOOGLE_API_KEY."""
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise GeminiError(
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    # Imported lazily so the rest of the app can be imported/tested without
    # the google-genai package installed.
    from google import genai

    _client = genai.Client(api_key=api_key)
    return _client


def generate(
    prompt: str,
    model: str = DEFAULT_GEMINI_MODEL,
    temperature: float = 0.7,
    system_instruction: Optional[str] = None,
) -> str:
    """
    Send a single-turn prompt to Gemini and return the text response.

    Args:
        prompt: The fully-rendered prompt (agent prompt template + trip context).
        model: Gemini model name.
        temperature: Sampling temperature.
        system_instruction: Optional system-level instruction for the model.

    Returns:
        The model's text response, stripped of leading/trailing whitespace.

    Raises:
        GeminiError: if the call fails after all retries.
    """
    client = _get_client()

    config = {"temperature": temperature}
    if system_instruction:
        config["system_instruction"] = system_instruction

    last_error: Optional[Exception] = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
            text = (response.text or "").strip()
            if not text:
                raise GeminiError("Gemini returned an empty response.")
            return text
        except Exception as exc:  # noqa: BLE001 - we deliberately catch broadly to retry
            last_error = exc
            logger.warning("Gemini call failed (attempt %d/%d): %s", attempt, _MAX_RETRIES, exc)
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF_SECONDS * attempt)

    raise GeminiError(f"Gemini call failed after {_MAX_RETRIES} attempts: {last_error}")
