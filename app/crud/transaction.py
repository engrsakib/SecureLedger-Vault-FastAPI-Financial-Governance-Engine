from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


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
    return db.query(Transaction).filter(Transaction.owner_id == owner_id).all()


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


def filter_transactions(
    db: Session,
    owner_id: int,
    type: str | None = None,
    category: str | None = None,
    minimum_amount: float | None = None,
    maximum_amount: float | None = None,
) -> list[Transaction]:
    query = db.query(Transaction).filter(Transaction.owner_id == owner_id)

    if type is not None:
        query = query.filter(Transaction.type == type)
    if category is not None:
        query = query.filter(Transaction.category == category)
    if minimum_amount is not None:
        query = query.filter(Transaction.amount >= minimum_amount)
    if maximum_amount is not None:
        query = query.filter(Transaction.amount <= maximum_amount)

    return query.all()
