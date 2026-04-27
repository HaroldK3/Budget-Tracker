from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from ..db import get_db
from API.models import User, UserCreate, Budget, BudgetCreate, BudgetCategory, BudgetCategoryCreate
from passlib.context import CryptContext #type: ignore
from werkzeug.security import generate_password_hash
import os
from datetime import datetime

router = APIRouter(prefix = "/budgets",  tags=["Budgets"])

## Pull current budget
##@router.get("/current", response_model=Budget)
##def get_current_budget(db: Session = Depends(get_db)):
##    budget = db.query(Budget).filter(Budget.user_id == User.user.id).first()
##    if not budget:
##        raise HTTPException(status_code=404, detail="Budget not found")
##    return budget

## pull all budgets
##@router.get("/all_budgets", response_model=list[Budget])
##def get_all_budgets(db: Session = Depends(get_db)):
##    budgets = db.query(Budget).filter(Budget.user_id == User.user.id | Budget.user_id == None).all()
##    return budgets

## Create A Budget -- WIP
##@router.post("/create", response_model=Budget)
##def create_budget(budget: BudgetCreate, budget_category: BudgetCategoryCreate, db: Session = Depends(get_db)):
##    new_budget = Budget(
##        name=budget.name,
##        created_at=datetime.utcnow(),
##        user_id=User.user.id
##    )
##    for i in range(4):
##        new_budget_category = BudgetCategory(
##            category_name=budget_category.category_name,
##            percentage=budget_category.percentage,
##            budget_id=new_budget.id
##        )

##    db.add(new_budget)
##    db.add(new_budget_category)
##    db.commit()
##    db.refresh(new_budget)
##    return new_budget
##
## Pull current budget
@router.get("/current")
def get_current_budget(user_id: int, db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.user_id == user_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget

## Pull all budgets for a user (including default/shared budgets)
@router.get("/all_budgets")
def get_all_budgets(user_id: int, db: Session = Depends(get_db)):
    budgets = db.query(Budget).filter(
        or_(Budget.user_id == user_id, Budget.user_id == None)
    ).all()
    return budgets

## Create a budget
@router.post("/create")
def create_budget(budget: BudgetCreate, budget_category: BudgetCategoryCreate, db: Session = Depends(get_db)):
    new_budget = Budget(
        name=budget.name,
        created_at=datetime.now(datetime.UTC),
        user_id=budget.user_id
    )
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)

    new_budget_category = BudgetCategory(
        category_name=budget_category.category_name,
        percentage=budget_category.percentage,
        budget_id=new_budget.id
    )
    db.add(new_budget_category)
    db.commit()

    return new_budget
