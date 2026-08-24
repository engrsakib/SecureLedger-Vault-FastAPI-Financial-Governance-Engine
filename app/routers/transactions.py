from datetime import date as DateType
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.links import transaction_links
from app.core.openapi_responses import PROTECTED_ERRORS, error_responses
from app.core.response import success_result
from app.crud import transaction as transaction_crud
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.envelope import ApiSuccessResponse
from app.schemas.transaction import (
    SortOrder,
    TransactionCreate,
    TransactionFilterRequest,
    TransactionListMeta,
    TransactionListQuery,
    TransactionResponse,
    TransactionSortField,
    TransactionUpdate,
)
from app.schemas.user import MessageResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _list_query_params(
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=100, description="Number of items per page")
    ] = 20,
    search: Annotated[
        str | None,
        Query(description="Search in title and category (case-insensitive)"),
    ] = None,
    type: Annotated[
        Literal["income", "expense"] | None,
        Query(description="Filter by type: income or expense"),
    ] = None,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    minimum_amount: Annotated[
        float | None, Query(description="Minimum amount (inclusive)")
    ] = None,
    maximum_amount: Annotated[
        float | None, Query(description="Maximum amount (inclusive)")
    ] = None,
    date_from: Annotated[
        DateType | None, Query(description="Transactions on or after this date")
    ] = None,
    date_to: Annotated[
        DateType | None, Query(description="Transactions on or before this date")
    ] = None,
    sort_by: Annotated[
        TransactionSortField, Query(description="Field to sort by")
    ] = "date",
    sort_order: Annotated[SortOrder, Query(description="Sort direction")] = "desc",
) -> TransactionListQuery:
    return TransactionListQuery(
        page=page,
        page_size=page_size,
        search=search,
        type=type,
        category=category,
        minimum_amount=minimum_amount,
        maximum_amount=maximum_amount,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def _filters_from_query(query: TransactionListQuery) -> dict:
    return query.model_dump(
        exclude_none=True,
        exclude={"page", "page_size", "sort_by", "sort_order"},
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a transaction",
    response_model=ApiSuccessResponse[TransactionResponse],
    responses=error_responses(*PROTECTED_ERRORS),
)
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
    return success_result(
        request,
        data=TransactionResponse.model_validate(transaction),
        message="Transaction created successfully",
        status_code=status.HTTP_201_CREATED,
        links=links,
        next_step={"action": "view", "url": links["self"]},
    )


@router.get(
    "",
    summary="List transactions with pagination, search, sort, and filters",
    response_model=ApiSuccessResponse[list[TransactionResponse]],
    responses=error_responses(*PROTECTED_ERRORS),
)
def get_transactions(
    request: Request,
    query: Annotated[TransactionListQuery, Depends(_list_query_params)],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transactions, total_items = transaction_crud.list_transactions(
        db,
        owner_id=current_user.id,
        page=query.page,
        page_size=query.page_size,
        search=query.search,
        type=query.type,
        category=query.category,
        minimum_amount=query.minimum_amount,
        maximum_amount=query.maximum_amount,
        date_from=query.date_from,
        date_to=query.date_to,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
    )
    data = [TransactionResponse.model_validate(item) for item in transactions]
    meta = TransactionListMeta.build(
        page=query.page,
        page_size=query.page_size,
        total_items=total_items,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
        filters=_filters_from_query(query),
    )
    return success_result(
        request,
        data=data,
        message="Transactions retrieved successfully",
        meta=meta.model_dump(),
        links=transaction_links(request),
    )


@router.post(
    "/filter",
    summary="Filter transactions (JSON body)",
    response_model=ApiSuccessResponse[list[TransactionResponse]],
    responses=error_responses(*PROTECTED_ERRORS),
)
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
    return success_result(
        request,
        data=data,
        message="Filtered transactions retrieved successfully",
        links=transaction_links(request),
    )


@router.get(
    "/filter",
    summary="Filter transactions (query params)",
    response_model=ApiSuccessResponse[list[TransactionResponse]],
    responses=error_responses(*PROTECTED_ERRORS),
)
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
    return success_result(
        request,
        data=data,
        message="Filtered transactions retrieved successfully",
        links=transaction_links(request),
    )


@router.get(
    "/{transaction_id}",
    summary="Get transaction by ID",
    response_model=ApiSuccessResponse[TransactionResponse],
    responses=error_responses(*PROTECTED_ERRORS),
)
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
    return success_result(
        request,
        data=TransactionResponse.model_validate(transaction),
        message="Transaction retrieved successfully",
        links=links,
    )


@router.put(
    "/{transaction_id}",
    summary="Update a transaction",
    response_model=ApiSuccessResponse[TransactionResponse],
    responses=error_responses(*PROTECTED_ERRORS),
)
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
    return success_result(
        request,
        data=TransactionResponse.model_validate(updated),
        message="Transaction updated successfully",
        links=links,
    )


@router.delete(
    "/{transaction_id}",
    summary="Delete a transaction",
    response_model=ApiSuccessResponse[MessageResponse],
    responses=error_responses(*PROTECTED_ERRORS),
)
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
    return success_result(
        request,
        data=MessageResponse(message="Transaction deleted successfully"),
        message="Transaction deleted successfully",
        links=links,
        next_step={"action": "list", "url": links["list"]},
    )
