from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from API.DB.db import get_db
from API.models import User
from flask import Flask, request, jsonify
from passlib.context import CryptContext
from werkzeug.security import generate_password_hash
import os

router = APIRouter(prefix="/user", tags=["User"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Existing user login
@router.post("/login")
def login_user(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found.")
    
    # Password verification
    if not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code="400", detail="Incorrect Password.")
    
    return {"message": f"Welcome {user.name}."}

# New user creation.
@router.post("/create_user")
def create_user(email: str, password: str, name: str, db: Session=Depends(get_db)):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use.")
    
    pass_hash = pwd_context.hash(password)

    new_user = User(email=email, password_hash=pass_hash, name=name)
    db.add(new_user)
    db.commit()
    db.refresh()

    return {"message": f"User {email} created."}
    
