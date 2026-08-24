from datetime import date as DateType
from math import ceil
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


TransactionSortField = Literal["id", "title", "amount", "date", "type", "category"]
SortOrder = Literal["asc", "desc"]


class TransactionListQuery(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: str | None = Field(
        default=None,
        description="Search in transaction title and category (case-insensitive)",
        examples=["groceries"],
    )
    type: Literal["income", "expense"] | None = Field(
        default=None, description="Filter by transaction type", examples=["expense"]
    )
    category: str | None = Field(
        default=None, description="Filter by exact category name", examples=["Food"]
    )
    minimum_amount: float | None = Field(
        default=None, description="Minimum amount (inclusive)", examples=[100.0]
    )
    maximum_amount: float | None = Field(
        default=None, description="Maximum amount (inclusive)", examples=[5000.0]
    )
    date_from: DateType | None = Field(
        default=None, description="Filter transactions on or after this date"
    )
    date_to: DateType | None = Field(
        default=None, description="Filter transactions on or before this date"
    )
    sort_by: TransactionSortField = Field(default="date", description="Sort field")
    sort_order: SortOrder = Field(default="desc", description="Sort direction")

    @field_validator("search")
    @classmethod
    def strip_search(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class TransactionListMeta(BaseModel):
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total matching transactions")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether a next page exists")
    has_previous: bool = Field(..., description="Whether a previous page exists")
    sort_by: TransactionSortField = Field(..., description="Applied sort field")
    sort_order: SortOrder = Field(..., description="Applied sort direction")
    filters: dict[str, Any] = Field(
        default_factory=dict, description="Applied filter and search parameters"
    )

    @classmethod
    def build(
        cls,
        *,
        page: int,
        page_size: int,
        total_items: int,
        sort_by: TransactionSortField,
        sort_order: SortOrder,
        filters: dict[str, Any],
    ) -> "TransactionListMeta":
        total_pages = ceil(total_items / page_size) if total_items else 0
        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1 and total_pages > 0,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters,
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
