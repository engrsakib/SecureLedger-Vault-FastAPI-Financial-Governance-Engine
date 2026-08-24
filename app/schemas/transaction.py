from datetime import date as DateType
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    title: str
    amount: float = Field(gt=0)
    type: Literal["income", "expense"]
    category: str
    date: DateType


class TransactionUpdate(BaseModel):
    title: str | None = None
    amount: float | None = Field(default=None, gt=0)
    type: Literal["income", "expense"] | None = None
    category: str | None = None
    date: DateType | None = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    amount: float
    type: str
    category: str
    date: DateType
    owner_id: int


class MessageResponse(BaseModel):
    message: str
