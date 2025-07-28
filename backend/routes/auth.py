# backend/routes/auth.py

import os
import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt

from models import User, Laboratory
from schemas import UserCreate, UserLogin, UserOut
from database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])

SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 2

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

@router.get("/admin-available")
def admin_available(db: Session = Depends(get_db)):
    admin_exists = db.query(User).filter(User.role == "ADMIN").first()
    return {"available": admin_exists is None}


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    # ✅ If user role is ADMIN, check if this lab already has one
    if user.role.upper() == "ADMIN":
        lab_admin = db.query(User).filter(
            User.role == "ADMIN",
            User.laboratory_id == user.laboratory_id
        ).first()
        if lab_admin:
            raise HTTPException(status_code=403, detail="This lab already has an Admin.")

    hashed_password = pwd_context.hash(user.password)
    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hashed_password,
        role=user.role.upper(),
        laboratory_id=user.laboratory_id  # ✅ attach lab
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user



@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.full_name == user.full_name).first()
    if not db_user or not pwd_context.verify(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if db_user.role != "SUPER_ADMIN":
        if not user.lab_name:
            raise HTTPException(status_code=400, detail="Lab name is required.")
        lab = db.query(Laboratory).filter(Laboratory.name == user.lab_name).first()
        if not lab:
            raise HTTPException(status_code=404, detail="Lab not found.")
        if db_user.laboratory_id != lab.id:
            raise HTTPException(status_code=403, detail="User does not belong to this lab.")

    token_data = {
        "sub": db_user.full_name,
        "role": db_user.role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }

    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": db_user.role,
        "user": {
            "id": db_user.id,
            "full_name": db_user.full_name,
            "email": db_user.email,
            "role": db_user.role
        }
    }