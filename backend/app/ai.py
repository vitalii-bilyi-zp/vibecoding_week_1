"""OpenRouter client. OpenRouter is OpenAI-compatible, so we use the openai SDK
pointed at the OpenRouter base URL. Config comes from the environment."""

import os

from openai import OpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b:free"


def get_model() -> str:
    return os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)


def get_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)


def ask(prompt: str) -> str:
    """Send a single user prompt and return the model's text reply."""
    client = get_client()
    completion = client.chat.completions.create(
        model=get_model(),
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content or ""
