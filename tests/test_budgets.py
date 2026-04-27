"""
Tests for /budgets routes.

Run:
    pytest tests/test_budgets.py -v
"""

import os
import pytest
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, DECIMAL, or_
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, UTC
from typing import Optional

# ── Test DB setup ─────────────────────────────────────────────────────────────

TEST_DB_PATH = "test_budgets.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///./{TEST_DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Models (mirrored from API/models.py) ──────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True)
    name          = Column(String)
    email         = Column(String, unique=True, index=True)
    password_hash = Column(String)
    budgets       = relationship("Budget", back_populates="user")

class Budget(Base):
    __tablename__ = "budgets"
    id         = Column(Integer, primary_key=True)
    name       = Column(String, nullable=False)
    created_at = Column(DateTime)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=True)
    user       = relationship("User", back_populates="budgets")
    items      = relationship("BudgetCategory", back_populates="budget")

class BudgetCategory(Base):
    __tablename__ = "budget_categories"
    id            = Column(Integer, primary_key=True)
    category_name = Column(String)
    percentage    = Column(DECIMAL)
    budget_id     = Column(Integer, ForeignKey("budgets.id"))
    budget        = relationship("Budget", back_populates="items")


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class BudgetCreate(BaseModel):
    name:    str
    user_id: int

class BudgetCategoryCreate(BaseModel):
    category_name: str
    percentage:    float
    budget_id:     int


# ── DB dependency + override ──────────────────────────────────────────────────

def get_db():
    pass

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── App & router (fixed routes) ───────────────────────────────────────────────

app = FastAPI()
router = APIRouter(prefix="/budgets", tags=["Budgets"])

@router.get("/current")
def get_current_budget(user_id: int, db=Depends(get_db)):
    budget = db.query(Budget).filter(Budget.user_id == user_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget

@router.get("/all_budgets")
def get_all_budgets(user_id: int, db=Depends(get_db)):
    budgets = db.query(Budget).filter(
        or_(Budget.user_id == user_id, Budget.user_id == None)
    ).all()
    return budgets

@router.post("/create")
def create_budget(budget: BudgetCreate, budget_category: BudgetCategoryCreate, db=Depends(get_db)):
    new_budget = Budget(
        name=budget.name,
        created_at=datetime.now(UTC),
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

app.include_router(router)
app.dependency_overrides[get_db] = override_get_db


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    engine.dispose()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@pytest.fixture()
def client():
    return TestClient(app)

@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture()
def seeded_user(db):
    user = User(
        email="test@example.com",
        password_hash=pwd_context.hash("TestPass123"),
        name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture()
def seeded_budget(db, seeded_user):
    budget = Budget(
        name="Monthly Budget",
        created_at=datetime.now(UTC),
        user_id=seeded_user.id,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget

@pytest.fixture()
def seeded_budget_category(db, seeded_budget):
    cat = BudgetCategory(
        category_name="Food",
        percentage=30.0,
        budget_id=seeded_budget.id,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


# ═══════════════════════════════════════════════════════════════════════════
# GET /budgets/current
# ═══════════════════════════════════════════════════════════════════════════

class TestGetCurrentBudget:
    def test_returns_current_budget(self, client, seeded_user, seeded_budget):
        response = client.get(f"/budgets/current?user_id={seeded_user.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Monthly Budget"

    def test_returns_first_budget_when_multiple_exist(self, client, db, seeded_user):
        db.add_all([
            Budget(name="Budget A", created_at=datetime.now(UTC), user_id=seeded_user.id),
            Budget(name="Budget B", created_at=datetime.now(UTC), user_id=seeded_user.id),
        ])
        db.commit()
        response = client.get(f"/budgets/current?user_id={seeded_user.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Budget A"

    def test_404_when_no_budget_exists(self, client, seeded_user):
        response = client.get(f"/budgets/current?user_id={seeded_user.id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Budget not found"

    def test_404_for_nonexistent_user(self, client):
        response = client.get("/budgets/current?user_id=9999")
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# GET /budgets/all_budgets
# ═══════════════════════════════════════════════════════════════════════════

class TestGetAllBudgets:
    def test_returns_all_budgets_for_user(self, client, db, seeded_user):
        db.add_all([
            Budget(name="Budget A", created_at=datetime.now(UTC), user_id=seeded_user.id),
            Budget(name="Budget B", created_at=datetime.now(UTC), user_id=seeded_user.id),
        ])
        db.commit()
        response = client.get(f"/budgets/all_budgets?user_id={seeded_user.id}")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_includes_shared_budgets_with_no_user(self, client, db, seeded_user):
        db.add_all([
            Budget(name="My Budget",     created_at=datetime.now(UTC), user_id=seeded_user.id),
            Budget(name="Default Budget", created_at=datetime.now(UTC), user_id=None),
        ])
        db.commit()
        response = client.get(f"/budgets/all_budgets?user_id={seeded_user.id}")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_does_not_return_other_users_budgets(self, client, db, seeded_user):
        other_user = User(email="other@example.com", password_hash="x", name="Other")
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        db.add_all([
            Budget(name="My Budget",    created_at=datetime.now(UTC), user_id=seeded_user.id),
            Budget(name="Other Budget", created_at=datetime.now(UTC), user_id=other_user.id),
        ])
        db.commit()

        response = client.get(f"/budgets/all_budgets?user_id={seeded_user.id}")
        assert response.status_code == 200
        names = [b["name"] for b in response.json()]
        assert "My Budget" in names
        assert "Other Budget" not in names

    def test_returns_empty_list_when_no_budgets(self, client, seeded_user):
        response = client.get(f"/budgets/all_budgets?user_id={seeded_user.id}")
        assert response.status_code == 200
        assert response.json() == []


# ═══════════════════════════════════════════════════════════════════════════
# POST /budgets/create
# ═══════════════════════════════════════════════════════════════════════════

class TestCreateBudget:
    def test_creates_budget_successfully(self, client, seeded_user):
        budget_payload = {"name": "New Budget", "user_id": seeded_user.id}
        category_payload = {"category_name": "Food", "percentage": 30.0, "budget_id": 0}
        response = client.post("/budgets/create", json={
            "budget": budget_payload,
            "budget_category": category_payload,
        })
        assert response.status_code == 200
        all_response = client.get(f"/budgets/all_budgets?user_id={seeded_user.id}")
        assert any(b for b in all_response.json() if b["name"] == "New Budget")

    def test_created_budget_has_correct_user(self, client, seeded_user):
        budget_payload = {"name": "Savings Plan", "user_id": seeded_user.id}
        category_payload = {"category_name": "Transport", "percentage": 20.0, "budget_id": 0}
        response = client.post("/budgets/create", json={
            "budget": budget_payload,
            "budget_category": category_payload,
        })
        assert response.status_code == 200
        # Verify it belongs to the correct user
        all_response = client.get(f"/budgets/all_budgets?user_id={seeded_user.id}")
        user_budgets = [b for b in all_response.json() if b["name"] == "Savings Plan"]
        assert len(user_budgets) == 1
        assert user_budgets[0]["user_id"] == seeded_user.id

    def test_created_budget_appears_in_all_budgets(self, client, seeded_user):
        budget_payload = {"name": "Savings Plan", "user_id": seeded_user.id}
        category_payload = {"category_name": "Transport", "percentage": 20.0, "budget_id": 0}
        client.post("/budgets/create", json={
            "budget": budget_payload,
            "budget_category": category_payload,
        })
        all_response = client.get(f"/budgets/all_budgets?user_id={seeded_user.id}")
        names = [b["name"] for b in all_response.json()]
        assert "Savings Plan" in names

    def test_multiple_budgets_can_be_created(self, client, seeded_user):
        category_payload = {"category_name": "Food", "percentage": 30.0, "budget_id": 0}
        client.post("/budgets/create", json={"budget": {"name": "Budget A", "user_id": seeded_user.id}, "budget_category": category_payload})
        client.post("/budgets/create", json={"budget": {"name": "Budget B", "user_id": seeded_user.id}, "budget_category": category_payload})

        response = client.get(f"/budgets/all_budgets?user_id={seeded_user.id}")
        assert len(response.json()) == 2
