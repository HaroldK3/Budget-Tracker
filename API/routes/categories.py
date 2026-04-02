from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from API.db import get_db
from API.models import Category, User
import os

router = APIRouter(prefix="/categories", tags=["categories"])

class CategoryCreate(BaseModel):
    name: str
    type: str  # "income" or "expense" | "need" | "want" | "savings_debt"

#def get_current_user() -> User:
    # Placeholder for actual authentication logic
    #raise HTTPException(status_code=401, detail="Not authenticated")
    #if user_id or null
    
@router.post("/categories/", response_model=dict)
def create_category(
    payload: CategoryCreate,
    user_id: int,
    db: Session = Depends(get_db),
    
):
    # prevent duplicate name for this user
    existing = (
        db.query(Category)
        .filter(
            Category.name == payload.name, Category.user_id == user_id
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="You already have this category")

    cat = Category(
        name=payload.name,
        type=payload.type,
        is_default=False,
        user_id=user_id,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)

    return {
        "id": cat.id,
        "name": cat.name,
        "type": cat.type,
        "is_default": cat.is_default,
        "user_id": cat.user_id,
    }

@router.get("/categories/", response_model=list[dict])
def list_categories(
   user_id: int, db: Session = Depends(get_db)):
    query = db.query(Category)
    
    cats = (
        db.query(Category)
        .filter(
            (Category.user_id == user_id) | (Category.is_default.is_(True))
        ).order_by(Category.name).all()
    )

    return [
        {
            "id": cat.id,
            "name": cat.name,
            "type": cat.type,
            "is_default": cat.is_default,
            "user_id": cat.user_id,
        }
        for cat in cats
    ]