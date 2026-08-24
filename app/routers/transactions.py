from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.links import transaction_links
from app.core.response import success_response
from app.crud import transaction as transaction_crud
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionFilterRequest,
    TransactionResponse,
    TransactionUpdate,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a transaction")
def create_transaction(
    request: Request,
    transaction_in: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = transaction_crud.create_transaction(
        db, transaction_in, owner_id=current_user.id
    )
    links = transaction_links(request, transaction.id)
    return success_response(
        request,
        data=TransactionResponse.model_validate(transaction),
        message="Transaction created successfully",
        status_code=status.HTTP_201_CREATED,
        links=links,
        next_step={"action": "view", "url": links["self"]},
    )


@router.get("", summary="List all transactions")
def get_transactions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transactions = transaction_crud.get_transactions_by_owner(
        db, owner_id=current_user.id
    )
    data = [TransactionResponse.model_validate(item) for item in transactions]
    return success_response(
        request,
        data=data,
        message="Transactions retrieved successfully",
        links=transaction_links(request),
    )


@router.post("/filter", summary="Filter transactions (JSON body)")
def filter_transactions_json(
    request: Request,
    filters: TransactionFilterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transactions = transaction_crud.filter_transactions(
        db,
        owner_id=current_user.id,
        type=filters.type,
        category=filters.category,
        minimum_amount=filters.minimum_amount,
        maximum_amount=filters.maximum_amount,
    )
    data = [TransactionResponse.model_validate(item) for item in transactions]
    return success_response(
        request,
        data=data,
        message="Filtered transactions retrieved successfully",
        links=transaction_links(request),
    )


@router.get("/filter", summary="Filter transactions (query params)")
def filter_transactions_query(
    request: Request,
    type: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    minimum_amount: Annotated[float | None, Query()] = None,
    maximum_amount: Annotated[float | None, Query()] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transactions = transaction_crud.filter_transactions(
        db,
        owner_id=current_user.id,
        type=type,
        category=category,
        minimum_amount=minimum_amount,
        maximum_amount=maximum_amount,
    )
    data = [TransactionResponse.model_validate(item) for item in transactions]
    return success_response(
        request,
        data=data,
        message="Filtered transactions retrieved successfully",
        links=transaction_links(request),
    )


@router.get("/{transaction_id}", summary="Get transaction by ID")
def get_transaction(
    request: Request,
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
    links = transaction_links(request, transaction_id)
    return success_response(
        request,
        data=TransactionResponse.model_validate(transaction),
        message="Transaction retrieved successfully",
        links=links,
    )


@router.put("/{transaction_id}", summary="Update a transaction")
def update_transaction(
    request: Request,
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
    updated = transaction_crud.update_transaction(db, transaction, transaction_in)
    links = transaction_links(request, transaction_id)
    return success_response(
        request,
        data=TransactionResponse.model_validate(updated),
        message="Transaction updated successfully",
        links=links,
    )


@router.delete("/{transaction_id}", summary="Delete a transaction")
def delete_transaction(
    request: Request,
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
    links = transaction_links(request)
    return success_response(
        request,
        data={"message": "Transaction deleted successfully"},
        message="Transaction deleted successfully",
        links=links,
        next_step={"action": "list", "url": links["list"]},
    )
