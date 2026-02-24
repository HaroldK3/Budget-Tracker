from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..db import get_db
from API.models import User, UserCreate, Transaction, TransactionCreate
from passlib.context import CryptContext #type: ignore
from werkzeug.security import generate_password_hash
import os
from datetime import datetime

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
@router.post("/add_transaction")
def add_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    new_transaction = Transaction(                         #type:ignore
        amount = transaction.amount,
        description=transaction.description,
        is_income = transaction.is_income,
        category_id = transaction.category_id,
        user_id = transaction.user_id,
        date = datetime.now()
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction

# Get transactions by UID
@router.get("/transactions/{user_id}")
def get_trans_by_user(user_id: int, db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()

    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found for user.")

    return transactions

# Get transactions by type

# Delete transaction

# Update transaction (**LAST**)

#Get category-summary (Adds all stuff spent in the diff categories)
