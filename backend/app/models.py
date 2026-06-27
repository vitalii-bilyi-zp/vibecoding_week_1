"""Pydantic models for the board API. These mirror the frontend BoardData shape."""

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
