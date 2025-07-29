from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models import Account, Transaction, User
from app.db import engine
from app.logger import logging
from app.schemas import TransactionCreate
from datetime import datetime

def make_transaction_service(transaction: TransactionCreate, current_user: User):
    with Session(engine) as session:
        from_acc = session.get(Account, transaction.from_account_id)
        to_acc = session.get(Account, transaction.to_account_id)
        if not from_acc or not to_acc:
            logging.warning(f"Transaction failed: invalid account(s) by user {current_user.username}")
            raise HTTPException(status_code=404, detail="Account not found")
        if from_acc.balance < transaction.amount:
            logging.warning(f"Transaction failed: Insufficient funds by user {current_user.username}")
            raise HTTPException(status_code=400, detail="Insufficient funds")
        if from_acc.user_id != current_user.id:
            logging.warning(f"Unauthorized transaction attempt by user {current_user.username} on account {from_acc.id}")
            raise HTTPException(status_code=403, detail="You can only send money from your own account")
        from_acc.balance -= transaction.amount
        to_acc.balance += transaction.amount
        db_transaction = Transaction(
            from_account_id=transaction.from_account_id,
            to_account_id=transaction.to_account_id,
            amount=transaction.amount,
            timestamp=datetime.utcnow()
        )
        session.add(db_transaction)
        session.commit()
        session.refresh(db_transaction)
        logging.info(f"Transaction: {transaction.amount} from {from_acc.id} to {to_acc.id} by user {current_user.username}")
        return db_transaction

def get_transactions_service(current_user: User):
    with Session(engine) as session:
        accounts = session.exec(select(Account.id).where(Account.user_id == current_user.id)).all()
        transactions = session.exec(
            select(Transaction).where(
                (Transaction.from_account_id.in_(accounts)) |
                (Transaction.to_account_id.in_(accounts))
            )
        ).all()
        return transactions