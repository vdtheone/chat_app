import os
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from config import SessionLocal
from chat.models.user_info import User

SECRET_KEY = os.environ.get('SECRET_KEY')
ALGORITHM = os.environ.get('ALGORITHM')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/chat/login")

def get_current_user(token: str = Depends(oauth2_scheme), db:Session = Depends(get_db)):
    credentials_exception = HTTPException(  
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        id = payload.get("id")
        user = db.query(User).get(id)
        if not user:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception
