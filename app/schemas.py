from pydantic import BaseModel, Field, validator
    

class UserCreate(BaseModel):
    username: str
    password: str

    @validator('password')
    def password_policy(cls, v):

        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')

        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')
        
        if not any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for char in v):
            raise ValueError('Password must contain at least one special character')
        
        return v


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
        
        # Remove unnecessary / dangerous chars
        unnecessary = ['<', '>', '"', "'", ';', '--']
        for char in unnecessary:
            if char in v:
                raise ValueError('Account name contains invalid characters')

        return v

    
class TransactionCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float = Field(gt=0) # amount must be > 0