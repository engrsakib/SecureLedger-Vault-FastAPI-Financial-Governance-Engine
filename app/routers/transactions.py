from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud import transaction as transaction_crud
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.transaction import (
    MessageResponse,
    TransactionCreate,
    TransactionFilterRequest,
    TransactionResponse,
    TransactionUpdate,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a transaction",
    description="Create a new income or expense record. Owner is set automatically from JWT.",
)
def create_transaction(
    transaction_in: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return transaction_crud.create_transaction(
        db, transaction_in, owner_id=current_user.id
    )


@router.get(
    "",
    response_model=list[TransactionResponse],
    summary="List all transactions",
    description="Return all transactions belonging to the authenticated user.",
)
def get_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return transaction_crud.get_transactions_by_owner(db, owner_id=current_user.id)


@router.post(
    "/filter",
    response_model=list[TransactionResponse],
    summary="Filter transactions (JSON body)",
    description="Filter transactions using a JSON request body. All filter fields are optional.",
)
def filter_transactions_json(
    filters: TransactionFilterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return transaction_crud.filter_transactions(
        db,
        owner_id=current_user.id,
        type=filters.type,
        category=filters.category,
        minimum_amount=filters.minimum_amount,
        maximum_amount=filters.maximum_amount,
    )


@router.get(
    "/filter",
    response_model=list[TransactionResponse],
    summary="Filter transactions (query params)",
    description="Filter transactions using query parameters. All filter fields are optional.",
)
def filter_transactions_query(
    type: Annotated[
        str | None,
        Query(description='Filter by type: "income" or "expense"', examples=["expense"]),
    ] = None,
    category: Annotated[
        str | None, Query(description="Filter by category name", examples=["Food"])
    ] = None,
    minimum_amount: Annotated[
        float | None, Query(description="Minimum amount (inclusive)", examples=[100.0])
    ] = None,
    maximum_amount: Annotated[
        float | None, Query(description="Maximum amount (inclusive)", examples=[5000.0])
    ] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return transaction_crud.filter_transactions(
        db,
        owner_id=current_user.id,
        type=type,
        category=category,
        minimum_amount=minimum_amount,
        maximum_amount=maximum_amount,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get transaction by ID",
    description="Return a single transaction. Returns 404 if not found or not owned by user.",
)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = transaction_crud.get_transaction(
        db, transaction_id, owner_id=current_user.id
    )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return transaction


@router.put(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Update a transaction",
    description="Update fields on an owned transaction. All body fields are optional.",
)
def update_transaction(
    transaction_id: int,
    transaction_in: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = transaction_crud.get_transaction(
        db, transaction_id, owner_id=current_user.id
    )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return transaction_crud.update_transaction(db, transaction, transaction_in)


@router.delete(
    "/{transaction_id}",
    response_model=MessageResponse,
    summary="Delete a transaction",
    description="Delete an owned transaction permanently.",
)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = transaction_crud.get_transaction(
        db, transaction_id, owner_id=current_user.id
    )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    transaction_crud.delete_transaction(db, transaction)
    return MessageResponse(message="Transaction deleted successfully")
