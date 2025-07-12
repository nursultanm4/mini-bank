from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    balance: float = 0.0

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    from_account_id: int = Field(foreign_key="account.id")
    to_account_id: int = Field(foreign_key="account.id")
    amount: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

