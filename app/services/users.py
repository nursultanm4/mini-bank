from sqlmodel import Session, select
from fastapi import HTTPException, status, Request
from app.models import User
from app.auth import hash_password, verify_password, create_access_token
from app.db import engine
from app.logger import logging
from app.schemas import UserCreate, Token



def register_user(user: UserCreate, request: Request):
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.username == user.username)).first()
        if existing:
            logging.warning(f"Attempt to register existing username: {user.username} from {request.client.host}")
            raise HTTPException(status_code=400, detail="Username already registered")
        hashed_pw = hash_password(user.password)
        db_user = User(username=user.username, hashed_password=hashed_pw)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        logging.info(f"New user registered: {user.username} from {request.client.host}")
        return db_user


def login_user(user: UserCreate, request: Request):
    with Session(engine) as session:
        db_user = session.exec(select(User).where(User.username == user.username)).first()
        if not db_user or not verify_password(user.password, db_user.hashed_password):
            logging.warning(f"Failed login attempt for username: {user.username} from {request.client.host}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        logging.info(f"Successful login for username: {user.username} from {request.client.host}")
        access_token = create_access_token(data={"sub": db_user.username})
        return Token(access_token=access_token, token_type="bearer")