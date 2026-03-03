from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from API.db import get_db
from API.models import Category

router = APIRouter(prefix="/categories", tags=["categories"])

class CategoryCreate(BaseModel):
    name: str
    type: str  # "income" or "expense" | "need" | "want" | "savings_debt"

@router.post("/", response_model=dict)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    # optional: prevent duplpicates on name
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    new_category = Category(
        name=category.name,
        type=category.type
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return {"message": "Category created successfully", "category": new_category}

    return {
        "id": new_category.id,
        "name": new_category.name,
        "type": new_category.type,
        "is_default": new_category.is_default
    }

@router.get("/", response_model=list[CategoryCreate])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.name).all()
    return [
        {
            "id": category.id,
            "name": category.name,
            "type": category.type,
            "is_default": category.is_default
        }
        for category in categories
    ]

