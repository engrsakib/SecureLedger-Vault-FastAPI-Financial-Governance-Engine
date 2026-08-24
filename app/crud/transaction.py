from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import Query, Session

from app.models.transaction import Transaction
from app.schemas.transaction import (
    SortOrder,
    TransactionCreate,
    TransactionSortField,
    TransactionUpdate,
)

SORT_COLUMNS: dict[TransactionSortField, object] = {
    "id": Transaction.id,
    "title": Transaction.title,
    "amount": Transaction.amount,
    "date": Transaction.date,
    "type": Transaction.type,
    "category": Transaction.category,
}


def create_transaction(
    db: Session, obj_in: TransactionCreate, owner_id: int
) -> Transaction:
    db_transaction = Transaction(
        title=obj_in.title,
        amount=obj_in.amount,
        type=obj_in.type,
        category=obj_in.category,
        date=obj_in.date,
        owner_id=owner_id,
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def get_transactions_by_owner(db: Session, owner_id: int) -> list[Transaction]:
    items, _ = list_transactions(db, owner_id=owner_id, page=1, page_size=10_000)
    return items


def get_transaction(
    db: Session, transaction_id: int, owner_id: int
) -> Transaction | None:
    return (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.owner_id == owner_id)
        .first()
    )


def update_transaction(
    db: Session, transaction: Transaction, obj_in: TransactionUpdate
) -> Transaction:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transaction, field, value)
    db.commit()
    db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, transaction: Transaction) -> None:
    db.delete(transaction)
    db.commit()


def _apply_transaction_filters(
    query: Query,
    *,
    search: str | None = None,
    type: str | None = None,
    category: str | None = None,
    minimum_amount: float | None = None,
    maximum_amount: float | None = None,
    date_from=None,
    date_to=None,
) -> Query:
    if search:
        term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(Transaction.title).like(term),
                func.lower(Transaction.category).like(term),
            )
        )
    if type is not None:
        query = query.filter(Transaction.type == type)
    if category is not None:
        query = query.filter(Transaction.category == category)
    if minimum_amount is not None:
        query = query.filter(Transaction.amount >= minimum_amount)
    if maximum_amount is not None:
        query = query.filter(Transaction.amount <= maximum_amount)
    if date_from is not None:
        query = query.filter(Transaction.date >= date_from)
    if date_to is not None:
        query = query.filter(Transaction.date <= date_to)
    return query


def list_transactions(
    db: Session,
    owner_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    type: str | None = None,
    category: str | None = None,
    minimum_amount: float | None = None,
    maximum_amount: float | None = None,
    date_from=None,
    date_to=None,
    sort_by: TransactionSortField = "date",
    sort_order: SortOrder = "desc",
) -> tuple[list[Transaction], int]:
    query = db.query(Transaction).filter(Transaction.owner_id == owner_id)
    query = _apply_transaction_filters(
        query,
        search=search,
        type=type,
        category=category,
        minimum_amount=minimum_amount,
        maximum_amount=maximum_amount,
        date_from=date_from,
        date_to=date_to,
    )

    sort_column = SORT_COLUMNS[sort_by]
    ordering = asc(sort_column) if sort_order == "asc" else desc(sort_column)
    query = query.order_by(ordering, Transaction.id.desc())

    total_items = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    return items, total_items


def filter_transactions(
    db: Session,
    owner_id: int,
    type: str | None = None,
    category: str | None = None,
    minimum_amount: float | None = None,
    maximum_amount: float | None = None,
) -> list[Transaction]:
    items, _ = list_transactions(
        db,
        owner_id=owner_id,
        page=1,
        page_size=10_000,
        type=type,
        category=category,
        minimum_amount=minimum_amount,
        maximum_amount=maximum_amount,
    )
    return items
