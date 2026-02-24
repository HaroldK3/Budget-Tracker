from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..db import get_db
from API.models import User, UserCreate, Transaction
from passlib.context import CryptContext #type: ignore
from werkzeug.security import generate_password_hash
import os

router = APIRouter(prefix = "/transaction",  tags=["Transaction"])

# Get current balance
@router.get("/balance")
def get_bal(user_id: int, db: Session = Depends(get_db)):
    income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.is_income == True
    ).scalar() or 0

    expenses = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.is_income == False
    ).scalar() or 0

    balance = income - expenses

    return {
        "user_id": user_id,
        "income": income,
        "expenses": expenses,
        "balance": balance
    }

# Add transaction


# Get transactions by UID

#Get transactions by type

# Delete transaction

# Update transaction

#Get category-summary (Adds all stuff spent in the diff categories)
