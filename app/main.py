from fastapi import FastAPI, HTTPException, Depends, status
from sqlmodel import Session, select
from .models import Account, Transaction, User
from .schemas import UserCreate, Token, AccountCreate, TransactionCreate
from .auth import hash_password, verify_password, create_access_token, get_current_user
from .db import engine, on_startup
from datetime import datetime

app = FastAPI()

@app.on_event("startup")
def startup():
    on_startup()

# Register
@app.post("/register/", response_model=User)
def register(user: UserCreate):
    with Session(engine) as session:
        # Check if user already exists
        existing = session.exec(select(User).where(User.username == user.username)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already registered")
        hashed_pw = hash_password(user.password)
        # CRUD ( Create, Read, Update, Delete )
        db_user = User(username=user.username, hashed_password=hashed_pw)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

# Login
@app.post("/login/", response_model=Token)
def login(user: UserCreate):
    with Session(engine) as session:
        db_user = session.exec(select(User).where(User.username == user.username)).first()
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = create_access_token(data={"sub": db_user.username})
        return Token(access_token=access_token, token_type="bearer")

# Create a new account
@app.post("/accounts/", response_model=Account)
def create_account(
    account: AccountCreate,
    current_user: User = Depends(get_current_user)
):
    with Session(engine) as session:
        db_account = Account(name=account.name, balance=account.balance)
        session.add(db_account)
        session.commit()
        session.refresh(db_account)
        return db_account

# Get account balance
@app.get("/accounts/{account_id}/balance")
def get_balance(account_id: int):
    with Session(engine) as session:
        account = session.get(Account, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        return {"account_id": account_id, "balance": account.balance}

# Make a transaction
@app.post("/transactions/", response_model=Transaction)
def make_transaction(transaction: TransactionCreate):
    with Session(engine) as session:
        from_acc = session.get(Account, transaction.from_account_id)
        to_acc = session.get(Account, transaction.to_account_id)
        if not from_acc or not to_acc:
            raise HTTPException(status_code=404, detail="Account not found")
        if from_acc.balance < transaction.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")
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
        return db_transaction

# List of all transactions
@app.get("/transactions/")
def get_transactions():
    with Session(engine) as session:
        transactions = session.exec(select(Transaction)).all()
        return transactions