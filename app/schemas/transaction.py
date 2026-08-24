from datetime import date as DateType
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Groceries",
                "amount": 150.0,
                "type": "expense",
                "category": "Food",
                "date": "2026-01-15",
            }
        }
    )

    title: str = Field(..., description="Transaction title", examples=["Groceries"])
    amount: float = Field(..., gt=0, description="Positive transaction amount", examples=[150.0])
    type: Literal["income", "expense"] = Field(
        ..., description="Transaction type", examples=["expense"]
    )
    category: str = Field(..., description="Category label", examples=["Food"])
    date: DateType = Field(..., description="Transaction date (YYYY-MM-DD)", examples=["2026-01-15"])


class TransactionUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Updated Groceries",
                "amount": 200.0,
                "type": "expense",
                "category": "Food",
                "date": "2026-01-15",
            }
        }
    )

    title: str | None = Field(default=None, description="Updated title", examples=["Updated Groceries"])
    amount: float | None = Field(
        default=None, gt=0, description="Updated amount (must be positive)", examples=[200.0]
    )
    type: Literal["income", "expense"] | None = Field(
        default=None, description="Updated type", examples=["expense"]
    )
    category: str | None = Field(default=None, description="Updated category", examples=["Food"])
    date: DateType | None = Field(
        default=None, description="Updated date (YYYY-MM-DD)", examples=["2026-01-15"]
    )


class TransactionFilterRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "expense",
                "category": "Food",
                "minimum_amount": 100.0,
                "maximum_amount": 5000.0,
            }
        }
    )

    type: Literal["income", "expense"] | None = Field(
        default=None, description="Filter by transaction type", examples=["expense"]
    )
    category: str | None = Field(
        default=None, description="Filter by category name", examples=["Food"]
    )
    minimum_amount: float | None = Field(
        default=None, description="Minimum amount (inclusive)", examples=[100.0]
    )
    maximum_amount: float | None = Field(
        default=None, description="Maximum amount (inclusive)", examples=[5000.0]
    )


class TransactionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Groceries",
                "amount": 150.0,
                "type": "expense",
                "category": "Food",
                "date": "2026-01-15",
                "owner_id": 1,
            }
        },
    )

    id: int = Field(..., description="Transaction ID")
    title: str = Field(..., description="Transaction title")
    amount: float = Field(..., description="Transaction amount")
    type: str = Field(..., description="Transaction type")
    category: str = Field(..., description="Category label")
    date: DateType = Field(..., description="Transaction date")
    owner_id: int = Field(..., description="Owner user ID")


class MessageResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Transaction deleted successfully"}}
    )

    message: str = Field(..., description="Success or status message")
