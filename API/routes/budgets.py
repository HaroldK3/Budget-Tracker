from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..db import get_db
from API.models import User, UserCreate, Budget, BudgetCreate, BudgetCategory, BudgetCategoryCreate
from passlib.context import CryptContext #type: ignore
from werkzeug.security import generate_password_hash
import os
from datetime import datetime

router = APIRouter(prefix = "/budgets",  tags=["Budgets"])

## Pull current budget
@router.get("/current", response_model=Budget)
def get_current_budget(db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.user_id == User.user.id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget

## pull all budgets
@router.get("/all_budgets", response_model=list[Budget])
def get_all_budgets(db: Session = Depends(get_db)):
    budgets = db.query(Budget).filter(Budget.user_id == User.user.id | Budget.user_id == None).all()
    return budgets

## Create A Budget -- WIP
@router.post("/create", response_model=Budget)
def create_budget(budget: BudgetCreate, budget_category: BudgetCategoryCreate, db: Session = Depends(get_db)):
    new_budget = Budget(
        name=budget.name,
        created_at=datetime.utcnow(),
        user_id=User.user.id
    )
    for i in range(4):
        new_budget_category = BudgetCategory(
            category_name=budget_category.category_name,
            percentage=budget_category.percentage,
            budget_id=new_budget.id
        )

    db.add(new_budget)
    db.add(new_budget_category)
    db.commit()
    db.refresh(new_budget)
    return new_budget