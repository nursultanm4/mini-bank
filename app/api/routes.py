from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlmodel import Session, select
from app.models import User, Account, Transaction
from app.schemas import UserCreate, Token, AccountCreate, TransactionCreate
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.db import engine
from app.logger import logging
from app.api.utils import login_key_func, register_key_func
from slowapi import Limiter
from slowapi.util import get_remote_address


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.on_event("startup")
def startup():
    from app.db import on_startup
    on_startup()


@router.post("/register/", response_model=User)
@limiter.limit("5/minute", key_func=register_key_func)
async def register(user: UserCreate, request: Request):
    from app.services.users import register_user
    return register_user(user, request)


@router.post("/login/", response_model=Token)
@limiter.limit("10/minute", key_func=login_key_func)
async def login(user: UserCreate, request: Request):
    from app.services.users import login_user
    return login_user(user, request)


@router.post("/accounts/", response_model=Account)
async def create_account(
    account: AccountCreate,
    current_user: User = Depends(get_current_user)
):
    from app.services.accounts import create_account_service
    return create_account_service(account, current_user)


@router.get("/accounts/{account_id}/balance")
async def get_balance(account_id: int, current_user: User = Depends(get_current_user)):
    from app.services.accounts import get_balance_service
    return get_balance_service(account_id, current_user)


@router.post("/transactions/", response_model=Transaction)
async def make_transaction(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user)
):
    from app.services.transactions import make_transaction_service
    return make_transaction_service(transaction, current_user)


@router.get("/transactions/")
async def get_transactions(current_user: User = Depends(get_current_user)):
    from app.services.transactions import get_transactions_service
    return get_transactions_service(current_user)