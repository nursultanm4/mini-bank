from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, create_engine, Session, select
from models import Account, Transaction

app = FastAPI()

# Setup db
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)

# Create tables 
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# Endpoint: Create a new account 
@app.post("/accounts/", response_model=Account)
def create_account(account: Account):
    with Session(engine) as session: # engine is our DB here
        session.add(account)
        session.commit()
        session.refresh(account)
        return account

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
def make_transaction(transaction: Transaction):
    with Session(engine) as session:
        from_acc = session.get(Account, transaction.from_account_id)
        to_acc = session.get(Account, transaction.to_account_id)

        if not from_acc or not to_acc:
            raise HTTPException(status_code=404, detail="Account not found")
        
        if from_acc.balance < transaction.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")
        
        from_acc.balance -= transaction.amount
        to_acc.balance += transaction.amount

        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        return transaction
    
# Endpoint: List of all transactions
@app.get("/transactions/")
def get_transactions():
    with Session(engine) as session:
        transactions = session.exec(select(Transaction)).all()
        return transactions
    
