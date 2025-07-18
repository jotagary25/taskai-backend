# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.domain.models import User
from app.api.schemas import UserCreate, UserLogin, UserRead, Token
from app.services.auth_services import hash_password, verify_password, create_token
from app.core.database import get_db

router = APIRouter()

@router.post("/register", response_model=UserRead)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, str(user.hashed_password)):
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    token = create_token({"sub": user.email})
    return Token(access_token=token)
