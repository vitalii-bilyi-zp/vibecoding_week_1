"""OpenRouter client. OpenRouter is OpenAI-compatible, so we use the openai SDK
pointed at the OpenRouter base URL. Config comes from the environment."""

import json
import os

from openai import OpenAI

from app.models import AIChatResponse, BoardData, ChatMessage, board_to_ai

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b:free"

CHAT_SYSTEM_PROMPT = """You are an assistant inside a Kanban project board app.
You help the user and may update the board.

Rules:
- Keep the existing column ids; you may rename column titles.
- You may add, edit, move, or remove cards. Give new cards a short unique id like "card-xyz".
- Respond with a single JSON object of exactly this shape:
  {
    "reply": "<a short message to the user>",
    "board_update": null OR {
      "columns": [
        {"id": "<column id>", "title": "<title>", "cards": [
          {"id": "<card id>", "title": "<title>", "details": "<details>"}
        ]}
      ]
    }
  }
- If you change the board, board_update must contain the COMPLETE new board (every
  column and every card), not just the changes.
- If you are only answering and not changing anything, set board_update to null."""

# Strict JSON schema for structured outputs. The array-based shape (no id-keyed
# maps) keeps it strict-compatible. board_update is required but nullable.
_AI_CARD_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "details": {"type": "string"},
    },
    "required": ["id", "title", "details"],
}

_AI_COLUMN_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "cards": {"type": "array", "items": _AI_CARD_SCHEMA},
    },
    "required": ["id", "title", "cards"],
}

CHAT_RESPONSE_SCHEMA = {
    "name": "chat_response",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "reply": {"type": "string"},
            "board_update": {
                "anyOf": [
                    {"type": "null"},
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "columns": {"type": "array", "items": _AI_COLUMN_SCHEMA}
                        },
                        "required": ["columns"],
                    },
                ]
            },
        },
        "required": ["reply", "board_update"],
    },
}


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


def chat_with_board(
    message: str, history: list[ChatMessage], board: BoardData
) -> AIChatResponse:
    """Ask the model about the board; it returns a reply and an optional update.

    Raises on a missing key (RuntimeError) or an unparseable/invalid response.
    """
    client = get_client()
    board_json = json.dumps(board_to_ai(board).model_dump())
    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "system", "content": f"Current board:\n{board_json}"},
        *[{"role": item.role, "content": item.content} for item in history],
        {"role": "user", "content": message},
    ]
    completion = client.chat.completions.create(
        model=get_model(),
        messages=messages,
        response_format={"type": "json_schema", "json_schema": CHAT_RESPONSE_SCHEMA},
    )
    content = completion.choices[0].message.content or "{}"
    return AIChatResponse.model_validate(json.loads(content))
