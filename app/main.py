from fastapi import FastAPI, HTTPException, Depends, status
from sqlmodel import Session, select
from app.models import Account, Transaction, User
from app.schemas import UserCreate, Token, AccountCreate, TransactionCreate
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.db import engine, on_startup
from datetime import datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi import Request
from slowapi.errors import RateLimitExceeded
from slowapi.extension import Limiter as LimiterExtension
import os
import logging


os.makedirs("logs", exist_ok=True)
# Configure logging
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


# Create limiter instance
limiter = Limiter(key_func=get_remote_address)


app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


async def login_key_func(request: Request):
    # Extract username from request body for Login
    try:
        body = await request.json()
        return body.get("username", get_remote_address(request)) # Fallback, dict.get(key, fallback_value)
    except Exception:
        return get_remote_address(request) # Fallback
        

async def register_key_func(request: Request):
    # Extract username from request body for Register
    try:
        body = await request.json()
        return body.get("username", get_remote_address(request))
    except Exception:
        return get_remote_address(request)    


@app.on_event("startup")
def startup():
    on_startup()


# Register  (limit: 5 requests per minute per username)
@app.post("/register/", response_model=User)
@limiter.limit("5/minute", key_func=register_key_func)
async def register(user: UserCreate, request: Request):
    with Session(engine) as session:
        # Check if user already exists
        existing = session.exec(select(User).where(User.username == user.username)).first() 
        if existing:
            logging.warning(f"Attempt to regiser existing username: {user.username} from {request.client.host}")
            raise HTTPException(status_code=400, detail="Username already registered")
        hashed_pw = hash_password(user.password)
        # CRUD ( Create, Read, Update, Delete )
        db_user = User(username=user.username, hashed_password=hashed_pw)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        logging.info(f"New user registered: {user.username} from {request.client.host}")
        return db_user


# Login  (limit: 10 requests per minute per username)
@app.post("/login/", response_model=Token)
@limiter.limit("10/minute", key_func=login_key_func)
async def login(user: UserCreate, request: Request):
    with Session(engine) as session:
        db_user = session.exec(select(User).where(User.username == user.username)).first()
        if not db_user:
            logging.warning(f"Failed login atttempt for username: {user.username} from {request.client.host}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        logging.info(f"Successful login for username: {user.username} from {request.client.host}")
        access_token = create_access_token(data={"sub": db_user.username})
        return Token(access_token=access_token, token_type="bearer")


# Create a new account
@app.post("/accounts/", response_model=Account)
async def create_account(
    account: AccountCreate,
    current_user: User = Depends(get_current_user)
):
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


# Get account balance
@app.get("/accounts/{account_id}/balance")
async def get_balance(account_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        account = session.get(Account, account_id)
        if not account:
            logging.warning(f"Account not found: {account_id} for user {current_user.username}")
            raise HTTPException(status_code=404, detail="Account not found")
        return {"account_id": account_id, "balance": account.balance}


# Make a transaction
@app.post("/transactions/", response_model=Transaction)
async def make_transaction(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user)
    ):
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


# List of all transactions
@app.get("/transactions/")
async def get_transactions(current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        # Get all accounts owned by the user
        user_accounts = session.exec(select(Account.id).where(Account.user_id==current_user.id)).first()
        # Get all transactions where the user is sender or receiver
        transactions = session.exec(
            select(Transaction).where(
                (Transaction.from_account_id.in_(user_accounts)) |
                (Transaction.to_account_id.in_(user_accounts))
            )
        ).all()
        return transactions