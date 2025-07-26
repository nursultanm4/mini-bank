from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    balance: float = 0.0
    user_id: int = Field(foreign_key="user.id")
    def __repr__(self):
        return f"<Account id={self.id} name={self.name} balance={self.balance} user_id={self.user_id}>"


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    from_account_id: int = Field(foreign_key="account.id")
    to_account_id: int = Field(foreign_key="account.id")
    amount: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    def __repr__(self):
        return f"<Transaction id={self.id} from={self.from_account_id} to={self.to_account_id} amount={self.amount}>"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"


