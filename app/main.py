from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, create_engine, Session, select
from models import Account, Transaction, User
from pydantic import BaseModel, Field, validator
from datetime import datetime
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # a config object

def hash_password(password: str) -> str:
    return pwd_context.hash(password) # .hash - a passlib method, creates a secure hash for passw

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT token utilities
from jose import JWTError, jwt
from datetime import timedelta

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Setup db
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)

# Create tables 
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# Registration and LOGIN 
from fastapi import Depends, status

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Endpoint: Register
@app.post("/register/", response_model=User)
def register(user: UserCreate):
    with Session(engine) as session: # engine is our DB here
        # Check if user already exists
        existing = session.exec(select(User).where(User.username == user.username)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already registered")
        hashed_pw = hash_password(user.password)
        db_user = User(username=user.username, hashed_password=hashed_pw)        
        session.add(db_user)
        session.commit()
        session.refresh()
        return db_user

# Endpoint: Login
@app.post("/login/", response_model=Token)
def login(user: UserCreate):
    with Session(engine) as session:
        db_user = session.exec(select(User).where(User.username == user.username)).first() # check DB if theres user with such data
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = create_access_token(data={"sub": db_user.username})
        return Token(access_token=access_token, token_type="bearer")


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=20)
    balance: float = Field(ge=0, default=0.0)

    @validator('name')
    def name_must_not_be_blank(cls, v):
        if not v.strip():
            raise ValueError('Name must not be blank')
        return v
    
class TransactionCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float = Field(gt=0) # amount must be > 0


# Endpoint: Create a new account 
@app.post("/accounts/", response_model=Account)
def create_account(account: AccountCreate):
    with Session(engine) as session: 
        # updated endpoint here
        db_account = Account(name=account.name, balance=account.balance)
        session.add(db_account)
        session.commit()
        session.refresh(db_account) 
        return db_account

# Endpoint: Get account balance
@app.get("/accounts/{account_id}/balance")
def get_balance(account_id: int):
    with Session(engine) as session:
        account = session.get(Account, account_id)

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return {"account_id": account_id, "balance": account.balance}
    
# Endpoint: Make a transaction
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
            timestamp=datetime.utcnow()  # always set datetime in backend
        )

        session.add(db_transaction)
        session.commit()
        session.refresh(db_transaction)
        return db_transaction
    
# Endpoint: List of all transactions
@app.get("/transactions/")
def get_transactions():
    with Session(engine) as session:
        transactions = session.exec(select(Transaction)).all()
        return transactions