from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from database import get_db
from models import User
import os
from sqlalchemy import or_

SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")  

# dependencies.py

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email_or_name = payload.get("sub")
        if email_or_name is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Try both full_name and email just to be safe
    user = db.query(User).filter(
    or_(User.email == email_or_name, User.full_name == email_or_name)
    ).first()

    if user is None:
        raise credentials_exception
    return user

def require_role(role: str):
    def role_checker(user: User = Depends(get_current_user)):
        if user.role.upper() != role.upper():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required role"
            )
        return user
    return role_checker


def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401, detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.full_name == username).first()
    if user is None:
        raise credentials_exception

    return user