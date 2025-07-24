from pydantic import BaseModel, Field, validator


class UserCreate(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


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