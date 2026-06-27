"""Pydantic models for the board and chat APIs. The board models mirror the
frontend BoardData shape; the AI models use an array-based board shape that is
simpler for the model to produce and validate."""

from typing import Literal

from pydantic import BaseModel, model_validator


class Card(BaseModel):
    id: str
    title: str
    details: str = ""


class Column(BaseModel):
    id: str
    title: str
    cardIds: list[str]


class BoardData(BaseModel):
    columns: list[Column]
    cards: dict[str, Card]

    @model_validator(mode="after")
    def check_consistency(self) -> "BoardData":
        # Every card key must match its card.id.
        for key, card in self.cards.items():
            if card.id != key:
                raise ValueError(f"card key {key!r} does not match card.id {card.id!r}")
        # Every referenced cardId must exist in the cards map.
        referenced = [card_id for column in self.columns for card_id in column.cardIds]
        missing = [card_id for card_id in referenced if card_id not in self.cards]
        if missing:
            raise ValueError(f"cardIds reference unknown cards: {missing}")
        return self


# --- Chat / AI models -------------------------------------------------------


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


# Board shape exchanged with the AI: cards are inlined as ordered arrays (no
# id-keyed maps), which is easier for the model to emit and to validate.
class AICard(BaseModel):
    id: str
    title: str
    details: str = ""


class AIColumn(BaseModel):
    id: str
    title: str
    cards: list[AICard] = []


class AIBoardUpdate(BaseModel):
    columns: list[AIColumn]


class AIChatResponse(BaseModel):
    reply: str
    board_update: AIBoardUpdate | None = None


class ChatResult(BaseModel):
    reply: str
    board_changed: bool


def board_to_ai(board: BoardData) -> AIBoardUpdate:
    """Convert the stored BoardData into the array-based AI shape."""
    columns = [
        AIColumn(
            id=column.id,
            title=column.title,
            cards=[
                AICard(**board.cards[card_id].model_dump())
                for card_id in column.cardIds
            ],
        )
        for column in board.columns
    ]
    return AIBoardUpdate(columns=columns)


def ai_to_board(update: AIBoardUpdate) -> BoardData:
    """Convert an AI board update back into BoardData (validates consistency)."""
    columns: list[Column] = []
    cards: dict[str, Card] = {}
    for column in update.columns:
        card_ids: list[str] = []
        for card in column.cards:
            cards[card.id] = Card(id=card.id, title=card.title, details=card.details)
            card_ids.append(card.id)
        columns.append(Column(id=column.id, title=column.title, cardIds=card_ids))
    return BoardData(columns=columns, cards=cards)
