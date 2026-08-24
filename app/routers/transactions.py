from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import transaction as transaction_crud
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.transaction import (
    MessageResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_in: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return transaction_crud.create_transaction(
        db, transaction_in, owner_id=current_user.id
    )


@router.get("", response_model=list[TransactionResponse])
def get_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return transaction_crud.get_transactions_by_owner(db, owner_id=current_user.id)


@router.get("/filter", response_model=list[TransactionResponse])
def filter_transactions(
    type: str | None = None,
    category: str | None = None,
    minimum_amount: float | None = None,
    maximum_amount: float | None = None,
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


@router.get("/{transaction_id}", response_model=TransactionResponse)
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


@router.put("/{transaction_id}", response_model=TransactionResponse)
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


@router.delete("/{transaction_id}", response_model=MessageResponse)
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
