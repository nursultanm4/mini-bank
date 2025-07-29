from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models import Account
from app.db import engine
from app.logger import logging
from app.schemas import AccountCreate
from app.models import User



def create_account_service(account: AccountCreate, current_user: User):
    with Session(engine) as session:
        db_account = Account(
            name=account.name,
            balance=account.balance,
            user_id=current_user.id
        )
        session.add(db_account)
        session.commit()
        session.refresh(db_account)
        return db_account


def get_balance_service(account_id: int, current_user: User):
    with Session(engine) as session:
        account = session.get(Account, account_id)
        if not account:
            logging.warning(f"Account not found: {account_id} for user {current_user.username}")
            raise HTTPException(status_code=404, detail="Account not found")
        if account.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this account")
        return {"account_id": account_id, "balance": account.balance}