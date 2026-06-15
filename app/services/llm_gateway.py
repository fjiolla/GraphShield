"""
LLM Gateway — Gemini-first with Groq fallback.
Provides a unified interface for LLM calls across the application.
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger("llm_gateway")


def _call_gemini(prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 2048) -> str:
    """Call Google Gemini API."""
    from google import genai

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")

    client = genai.Client(api_key=api_key)

    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=full_prompt,
    )
    return response.text


def _call_groq(prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 2048, json_mode: bool = False) -> str:
    """Call Groq API as fallback."""
    from groq import Groq

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")

    client = Groq(api_key=api_key)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    kwargs = {
        "messages": messages,
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def llm_generate(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> tuple[str, str]:
    """
    Generate text using Gemini first, fall back to Groq on failure.
    Returns a tuple of (response_text, provider_name).
    """
    # Try Gemini first
    try:
        result = _call_gemini(prompt, system_prompt, max_tokens)
        logger.info("LLM response from Gemini")
        return result, "gemini"
    except Exception as e:
        logger.warning("Gemini failed (%s), falling back to Groq", str(e)[:100])

    # Fallback to Groq
    try:
        result = _call_groq(prompt, system_prompt, max_tokens, json_mode)
        logger.info("LLM response from Groq (fallback)")
        return result, "groq"
    except Exception as e:
        logger.error("Both Gemini and Groq failed: %s", str(e))
        raise RuntimeError(f"All LLM providers failed. Last error: {str(e)}")


def llm_generate_json(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 2048,
) -> dict:
    """
    Generate a JSON response. Tries Gemini first, then Groq with json_mode.
    Returns parsed dict.
    """
    raw, _ = llm_generate(prompt, system_prompt, max_tokens, json_mode=True)

    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object in the response
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except json.JSONDecodeError:
                pass
        return {"raw_response": raw, "error": "Failed to parse JSON from LLM"}
