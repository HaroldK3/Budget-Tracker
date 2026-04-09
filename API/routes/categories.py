from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from API.db import get_db
from API.models import Category, User
import os

router = APIRouter(prefix="/categories", tags=["categories"])
class CategoryCreate(BaseModel):
    name: str
    type: str

@router.post("/", response_model=dict)
def create_category(
    payload: CategoryCreate,
    user_id: int,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(Category)
        .filter(
            Category.name == payload.name,
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="You already have this category")

    cat = Category(
        name=payload.name,
        type=payload.type,
        is_default=False,
    )

    db.add(cat)
    db.commit()
    db.refresh(cat)

    return {
        "id": cat.id,
        "name": cat.name,
        "type": cat.type,
        "is_default": cat.is_default,
    }

## pull all
@router.get("/")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return categories

## get one
@router.get("/{category_id}")
def get_one(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(
        Category.id == category_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category